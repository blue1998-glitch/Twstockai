"""Explicit engineering candidate, not an approved strategy or trade signal."""
from decimal import Decimal, localcontext, ROUND_HALF_EVEN

VERSION = 'macd-12-26-9-sma-seed/0.1'
PARAMETERS = dict(fast=12, slow=26, signal=9, ema_seed='FULL_WINDOW_SMA',
                  histogram='2 * (DIF - DEA)', precision=50, rounding='ROUND_HALF_EVEN',
                  warmup='26 price records for DIF; 34 for DEA/histogram',
                  missing_price='RESET_AND_REWARM', raw_action='RESET_AND_REWARM',
                  status='ENGINEERING_CANDIDATE_NOT_USER_APPROVED_STRATEGY')


def macd(closes, *, resets=(), fast=12, slow=26, signal=9):
    if any(type(n) is not int or n < 1 for n in (fast, slow, signal)) or fast >= slow:
        raise ValueError('Positive integer fast < slow and signal required')
    resets = set(resets)
    result, samples, differences = [], [], []
    ema_fast = ema_slow = dea = None
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_EVEN
        for index, raw in enumerate(closes):
            if index in resets or raw is None:
                samples, differences = [], []
                ema_fast = ema_slow = dea = None
            if raw is None:
                result.append(dict(dif=None, dea=None, histogram=None, reason='MISSING_PRICE_RESET'))
                continue
            value = Decimal(str(raw).replace(',', ''))
            if not value.is_finite():
                raise ValueError('Finite close required')
            samples.append(value)
            if len(samples) == fast:
                ema_fast = sum(samples) / fast
            elif len(samples) > fast:
                ema_fast += Decimal(2) / (fast + 1) * (value - ema_fast)
            if len(samples) == slow:
                ema_slow = sum(samples) / slow
            elif len(samples) > slow:
                ema_slow += Decimal(2) / (slow + 1) * (value - ema_slow)
            dif = None if ema_slow is None else ema_fast - ema_slow
            if dif is not None:
                differences.append(dif)
                if len(differences) == signal:
                    dea = sum(differences) / signal
                elif len(differences) > signal:
                    dea += Decimal(2) / (signal + 1) * (dif - dea)
            histogram = None if dea is None else 2 * (dif - dea)
            result.append(dict(dif=None if dif is None else format(dif, 'f'),
                               dea=None if dea is None else format(dea, 'f'),
                               histogram=None if histogram is None else format(histogram, 'f'),
                               reason='AVAILABLE' if histogram is not None else 'FULL_WINDOW_WARMUP'))
    return result
