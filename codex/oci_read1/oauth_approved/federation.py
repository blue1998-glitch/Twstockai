"""One-shot GitHub OIDC -> OCI RPST -> existing pilot SDK list adapter.
No IAM writes, key files, SDK retries, OAuth access-token substitution or CLI.
"""
import base64,hashlib,json,logging,os,re,time,urllib.request,urllib.error,urllib.parse
from codex.oci_ctrl1.handler import REPO,REPO_ID,OWNER_ID,Refused,strict
from codex.oci_bridge1.bridge import OCIReadAdapter,sanitize
ISSUER="https://token.actions.githubusercontent.com"
JWKS=ISSUER+"/.well-known/jwks"
AUDIENCE="twstockai-oci-read1"
RESOURCE_TYPE="githubactions"
SAFE_ERRORS={"NotAuthenticated","NotAuthorizedOrNotFound","Forbidden","TooManyRequests","InternalError","ServiceUnavailable","InvalidParameter"}
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*a,**k):return None

def validate_config(c):
    fields={"schema","domain_url","client_id","region","pilot_compartment","availability_domains"}
    if not isinstance(c,dict) or set(c)!=fields or c["schema"]!="read1-server-config/0.2":raise Refused("READ1_SERVER_CONFIG_UNKNOWN")
    if not isinstance(c["domain_url"],str) or not re.fullmatch(r"https://idcs-[a-zA-Z0-9]+\.identity\.oraclecloud\.com",c["domain_url"]):raise Refused("READ1_DOMAIN_ENDPOINT")
    if not isinstance(c["region"],str) or not re.fullmatch(r"[a-z]{2}-[a-z]+(?:-[a-z]+)*-[1-9][0-9]*",c["region"]):raise Refused("READ1_REGION")
    if not isinstance(c["pilot_compartment"],str) or not re.fullmatch(r"ocid1\.compartment\.oc1\.\.[A-Za-z0-9]+",c["pilot_compartment"]):raise Refused("READ1_EXISTING_PILOT_REQUIRED")
    ads=c["availability_domains"]
    if not isinstance(ads,list) or not 1<=len(ads)<=8 or len(ads)!=len(set(ads)) or any(not isinstance(a,str) or not re.fullmatch(r"[A-Za-z0-9:_-]{3,120}",a) for a in ads):raise Refused("READ1_ADS_UNKNOWN")
    if not isinstance(c["client_id"],str) or not re.fullmatch(r"[A-Za-z0-9_-]{8,200}",c["client_id"]):raise Refused("READ1_OAUTH_CLIENT")
    return c

def json_https(url,headers,data=None,limit=65536):
    req=urllib.request.Request(url,headers=headers,data=data)
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=15) as r:
        raw=r.read(limit+1)
        if r.status!=200 or len(raw)>limit:raise Refused("READ1_RESPONSE_BOUND_OR_STATUS")
        return strict(raw)

def request_job_token():
    url=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL","");access=os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    u=urllib.parse.urlparse(url)
    if u.scheme!="https" or u.username or u.password or u.port not in (None,443) or not u.hostname or not u.hostname.endswith(".actions.githubusercontent.com") or not access:raise Refused("READ1_NATIVE_OIDC_UNAVAILABLE")
    sep="&" if u.query else "?"
    obj=json_https(url+sep+"audience="+urllib.parse.quote(AUDIENCE,safe=""),{"Authorization":"Bearer "+access})
    token=obj.get("value")
    if not isinstance(token,str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",token) or len(token)>16384:raise Refused("READ1_NATIVE_OIDC_INVALID")
    return token

def verify_job_token(token,context,now,keys=None):
    import jwt
    if keys is None:keys=json_https(JWKS,{},limit=262144)
    try:
        header=jwt.get_unverified_header(token)
        if header.get("alg")!="RS256" or not isinstance(keys.get("keys"),list):raise ValueError()
        matches=[k for k in keys["keys"] if k.get("kid")==header.get("kid") and k.get("kty")=="RSA" and k.get("use","sig")=="sig"]
        if len(matches)!=1:raise ValueError()
        key=jwt.PyJWK.from_dict(matches[0],algorithm="RS256").key
        claims=jwt.decode(token,key,algorithms=["RS256"],issuer=ISSUER,audience=AUDIENCE,options={"require":["exp","iat","nbf","iss","aud","sub","jti"],"verify_exp":False,"verify_iat":False,"verify_nbf":False})
        if any(type(claims[x]) is not int for x in ("exp","iat","nbf")) or not claims["iat"]<=now<claims["exp"] or claims["nbf"]>now or not 0<claims["exp"]-claims["iat"]<=600:raise ValueError()
        expected={"repository":REPO,"repository_id":str(REPO_ID),"repository_visibility":"private","actor_id":str(OWNER_ID),"event_name":"issue_comment","ref":"refs/heads/main","workflow_ref":REPO+"/.github/workflows/read1.yml@refs/heads/main","workflow_sha":context["GITHUB_WORKFLOW_SHA"],"run_id":context["GITHUB_RUN_ID"],"run_attempt":"1","sub":"repo:"+REPO+":ref:refs/heads/main"}
        if any(claims.get(k)!=v for k,v in expected.items()):raise ValueError()
        return claims
    except Exception:raise Refused("READ1_OIDC_SIGNATURE_OR_CLAIMS")

def exchange_form(token,public_pem):
    return urllib.parse.urlencode({"grant_type":"urn:ietf:params:oauth:grant-type:token-exchange","requested_token_type":"urn:oci:token-type:oci-rpst","subject_token_type":"jwt","subject_token":token,"public_key":public_pem,"res_type":RESOURCE_TYPE,"rpst_exp":"5"}).encode()

def error_projection(status,code,request_id):
    return {"http_status":status if type(status) is int and 100<=status<=599 else None,"code":code if isinstance(code,str) and code in SAFE_ERRORS|{"invalid_client","invalid_grant","unauthorized_client","unsupported_grant_type","invalid_request"} else "UNCLASSIFIED_REDACTED","request_id_sha256":hashlib.sha256(request_id.encode()).hexdigest() if isinstance(request_id,str) and 1<=len(request_id)<=1024 else None}

class ObservedClient:
    def __init__(self,client,methods,proof,deadline):self.client,self.methods,self.proof,self.deadline=client,methods,proof,deadline
    def __getattr__(self,name):
        if name not in self.methods:raise Refused("READ1_LIST_ONLY")
        method=getattr(self.client,name);operation=self.methods[name]
        def call(**kw):
            if len(self.proof)>=32 or time.monotonic()>self.deadline:raise Refused("READ1_CALL_OR_TIME_BOUND")
            try:
                response=method(**kw)
                self.proof.append(dict(operation=operation,**error_projection(response.status,"OK",response.headers.get("opc-request-id"))))
                self.proof[-1]["code"]="OK"
                return response
            except Exception as e:
                import oci
                if isinstance(e,oci.exceptions.ServiceError):
                    self.proof.append(dict(operation=operation,**error_projection(e.status,e.code,getattr(e,"request_id",None))))
                else:self.proof.append(dict(operation=operation,http_status=None,code="TRANSPORT_OR_SDK_ERROR_REDACTED",request_id_sha256=None))
                raise
        return call

def control_plane_call_count(proof):
    # A timeout or SDK validation error is not proof that Oracle received a call.
    return len(proof) if all(type(x.get("http_status")) is int for x in proof) else "UNKNOWN"

def control_plane_status(proof):
    return "ACTUAL_API_RESPONSES" if any(type(x.get("http_status")) is int for x in proof) else "UNKNOWN"

def execute(config,context,now):
    logging.disable(logging.CRITICAL)
    secret=None;token=None;rpst=None;key=None
    proof=[];exchange_started=False;exchange_responded=False
    try:
        validate_config(config)
        token=request_job_token();claims=verify_job_token(token,context,time.time())
        # Only now read the approved dedicated OAuth secret; no API key fallback.
        secret=os.environ.get("OCI_READ1_CLIENT_SECRET")
        if not isinstance(secret,str) or not 16<=len(secret)<=4096:raise Refused("READ1_OAUTH_SECRET_NOT_CONFIGURED")
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        public=key.public_key().public_bytes(serialization.Encoding.PEM,serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        basic=base64.b64encode((config["client_id"]+":"+secret).encode()).decode()
        exchange_started=True
        obj=json_https(config["domain_url"]+"/oauth2/v1/token",{"Authorization":"Basic "+basic,"Content-Type":"application/x-www-form-urlencoded"},exchange_form(token,public))
        exchange_responded=True
        rpst=obj.get("token") # The documented RPST field, never access_token.
        if not isinstance(rpst,str) or not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",rpst):raise Refused("READ1_NOT_AN_OCI_RPST")
        import jwt
        body=jwt.decode(rpst,options={"verify_signature":False}) # TLS response; not used as an independent identity proof.
        if type(body.get("exp")) is not int or not time.time()<body["exp"]<=time.time()+360:raise Refused("READ1_RPST_LIFETIME")
        import oci
        signer=oci.auth.signers.SecurityTokenSigner(rpst,key)
        adapter=OCIReadAdapter.from_oci_sdk({"region":config["region"]},signer,config["pilot_compartment"],config["availability_domains"])
        endpoint="https://iaas."+config["region"]+".oraclecloud.com"
        for client in [adapter.compute,adapter.block]:
            if client.base_client.endpoint.rstrip("/")!=endpoint:raise Refused("READ1_OCI_ENDPOINT")
            client.base_client.session.max_redirects=0
        deadline=time.monotonic()+90
        adapter.compute=ObservedClient(adapter.compute,{"list_instances":"ListInstances"},proof,deadline)
        adapter.block=ObservedClient(adapter.block,{"list_boot_volumes":"ListBootVolumes","list_volumes":"ListVolumes"},proof,deadline)
        result=sanitize(adapter.read("list_pilot_compartment_resources"))
        status="OCI_READ_OK" if result["status"]=="KNOWN" else "OCI_READ_PARTIAL_OR_REFUSED"
        return dict(status=status,oracle_status=control_plane_status(proof),oracle_calls=control_plane_call_count(proof),sdk_list_attempts=len(proof),identity_exchange_calls=1,source="OCI_CONTROL_PLANE_RPST_SIGNED_SDK",result=result,official_responses=proof,oidc_claims_checked=True,account_evidence="OWNER_CONSOLE_OBSERVATION_NOT_ORACLE_API")
    except urllib.error.HTTPError as e:
        if not exchange_started:
            return dict(status="READ1_BLOCKED",reason="GITHUB_OIDC_SOURCE_HTTP_REFUSED",oracle_status="NOT_CONNECTED",oracle_calls=0,identity_exchange_calls=0)
        raw=e.read(65537);code=None
        try:code=strict(raw).get("error")
        except Exception:pass
        safe=error_projection(e.code,code,e.headers.get("opc-request-id"))
        return dict(status="OCI_EXCHANGE_REFUSED",oracle_status="ACTUAL_TOKEN_ENDPOINT_REFUSAL",oracle_calls=0,identity_exchange_calls=1,source="OCI_IDENTITY_DOMAIN_TOKEN_ENDPOINT",official_refusal=safe)
    except Refused as e:
        return dict(status="READ1_BLOCKED",reason=str(e),oracle_status="NOT_CONNECTED" if not proof else "UNKNOWN",oracle_calls=control_plane_call_count(proof),sdk_list_attempts=len(proof),identity_exchange_calls=(1 if exchange_responded else "UNKNOWN") if exchange_started else 0,official_responses=proof)
    except Exception:
        return dict(status="READ1_EXECUTION_OUTCOME_UNKNOWN",reason="REDACTED_NO_RETRY",oracle_status="UNKNOWN",oracle_calls=control_plane_call_count(proof),sdk_list_attempts=len(proof),identity_exchange_calls=(1 if exchange_responded else "UNKNOWN") if exchange_started else 0,official_responses=proof)
    finally:
        # Avoid persistent key/token files. Python cannot guarantee RAM zeroization.
        secret=token=rpst=key=None
