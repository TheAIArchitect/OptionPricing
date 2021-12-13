import numpy as np
import scipy.stats
from scipy.stats import norm


class BlackScholesMerton:

    '''
    Andrew W.E. McDonald, 2021-12-11

    References:
        - https://brilliant.org/wiki/black-scholes-merton/
        - https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model
        - https://www.youtube.com/watch?v=TnS8kI_KuJc&t=702s - MIT OCW Black-Scholes Formula, Risk-neutral Valuation
        - https://www.youtube.com/watch?v=spkim5Ns304 - How to interpret N(d1) and N(d2) in Black Scholes
        - Tim Worrall's PDF on Black Scholes in resources/papers
        - Black & Scholes' 1973 paper, The Pricing of Options and Corporate Liabilities in resources/papers

    sigma -  IV;
        - IV is the expected annualized standard deviation of the (log) return on the asset
        - Expressed as a percentage move from the mean
        - Divide by sqrt of number of trading days (around 256, so 16) to get implied daily move
    r - risk free rate
    S - *present value* price of underlying (This has been discounted in the equation)
    K - option strike, *future value* -> must be discounted. That is what the e^(-rt) does. Continuously compounds the discount rate back to present value.
    yte - years to expiry (convention seems to be by 365, not number of trading days -- in that case, maybe you'd want sqrt of trading )
    d1, d2 - essentially z-scores
    N - CDF of normal distribution

    d1:
        - SN(d1) is conditional expectation of the underlying at the expiration, discounted back to present value, given that the option expires in the money

    d2:
        - N(d2) is the probability that the underlying price will be at or above the strike at expiration

    ---
    - Ito's Formula / Lemma - basically a stochastic version of Taylor Series
    - Brownian Motion requires std. dev. to be sqrt of dt (delta t)
    - Black Scholes assumes IV is the same for all options at all strikes at a given expiry.
        - In reality, there is a smile shape (volatility smile), where it increases as the strike price moves away from the price of the underlying
    - Put-Call parity (T = time at expiry, t = now):
        - C(T) - P(T) - S(T) = -K
        - C(t) - P(t) - S(t) = -Ke^(-r[T-t])
            - Discount to curren value
    '''

    def __init__(me):
        pass

    def priceOption(me, type: str, sigma, yte, S, K, r):
        '''
        This computes and returns the Black Scholes Merton option price,
        rounded to 4 decimal places.
        '''
        d1 = me.computeD1(sigma, yte, S, K, r)
        d2 = me.computeD2FromD1(d1, sigma, yte)
        #print(f"d1: {d1}, d2: {d2}")
        presentValue = 0
        if type == 'C':
            presentValue = norm.cdf(d1)*S - norm.cdf(d2)*K*np.exp(-r*yte)
        elif type == 'P':
            presentValue = norm.cdf(-d2)*K*np.exp(-r*yte) - norm.cdf(-d1)*S
        return round(presentValue, 4)


    def computeD1(me, sigma, yte, S, K, r):
        return (np.log(S/K) + (r + (sigma**2/2))*yte)/(sigma*np.sqrt(yte))

    def computeD2FromD1(me, d1, sigma, yte):
        return d1 - sigma*np.sqrt(yte)

    def computeD2(me, sigma, yte, S, K, r):
        ''' This is the same as .computeD2FromD1() '''
        return (np.log(S/K) + (r - (sigma**2/2))*yte)/(sigma*np.sqrt(yte))

if __name__ == "__main__":
    ''' Test implementation. '''
    bsm = BlackScholesMerton()
    S = 50
    K = 45
    sigma = .3
    r = .02
    yte = 80/365 # Or should this be trading days (e.g., 250-256)?

    optionValue = bsm.priceOption('C', sigma, yte, S, K, r)
    print(f"Option worth ${optionValue}")

    d1 = bsm.computeD1(sigma, yte, S, K, r)
    d2 = bsm.computeD2FromD1(d1, sigma, yte)
    #altD2 = bs.computeD2(sigma, yte, S, K, r)
    #print(f"D1: {d1}, D2: {d2}, altD2: {altD2}")
    print(f"d1: {d1}, N(d1): {norm.cdf(d1)}, d2: {d2}, N(d2): {norm.cdf(d2)}")

