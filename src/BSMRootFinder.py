import numpy as np
import scipy.stats

from src.BlackScholesMerton import BlackScholesMerton

class BSMRootFinder:
    '''
    Andrew W.E. McDonald, 2021-12-11

    Calculates an option's IV using the Black-Scholes pricing model and a bisection--based approach.

    I looked at  Dekker's and Brent's methods, and realized the bisection portion of Dekker's method should be enough to do what needs to be done here.
        (with a slight modification).
        See: https://en.wikipedia.org/wiki/Brent%27s_method


    ---

    I got the idea to subtract the current price from the price computed with the guessed sigma (to create a root) from the below link,
        that was showing how to find IV using the Newton Raphson method.
        See: http://kevinpmooney.blogspot.com/2017/07/calculating-implied-volatility-from.html

    to verify my approach, I used some code I got from StackOverflow that implemented the Newton Raphson method.
    See David Duarte's answer: https://stackoverflow.com/questions/61289020/fast-implied-volatility-calculation-in-python

    '''

    def __init__(me):
        me.bs = BlackScholesMerton()



    def getBSIV(me, currentPrice: float, type: str, yte: float, S: float, K: int, r: float, initialIVGuess: float = 1):
        '''
        :param currentPrice: current price of option
        :param type: "P" or "C" (put/call)
        :param yte: years to expiration, float
        :param S: current price of underlying
        :param K: strike of option
        :param r: risk-free rate
        :param initialIVGuess: first guess at what the IV is; defaults to 5,000%
            Default value is 5,000% because it seems to be about the max volatility that makes a different to Black-Scholes.
            We need to make sure it will always be greater than the IV we're looking for.
        :return: 
        '''
        testEpsilon = 1e-4 # We want to be accurate to within 1/100th of $0.01
        sigmaGuess = initialIVGuess
        estimatedPrice = me.bs.priceOption(type, sigmaGuess, yte, S, K, r)
        testResult = estimatedPrice - currentPrice
        sigmaLow = 1e-6 # Can't be 0, or we'll get a division by zero error
        sigmaHigh = sigmaGuess
        iterations = 1 # We just did the first one
        maxIters = 100
        while np.abs(testResult) > testEpsilon and iterations < maxIters:
            # Find the midpoint of the difference between the upper and lower vol bounds
            sigmaGuess = (sigmaLow + sigmaHigh) / 2.0
            # Find the price estimate using that estimated vol, and then find the difference
            estimatedPrice = me.bs.priceOption(type, sigmaGuess, yte, S, K, r)
            testResult = estimatedPrice - currentPrice
            if testResult > 0: # Our IV guess is too high, so sigmaGuess becomes our new upper bound, and leave sigmaLow alone.
                sigmaHigh = sigmaGuess
            elif testResult < 0: # Our IV guess is too low, so sigmaGuess becomes our new lower bound. Leave sigmaHigh alone.
                sigmaLow = sigmaGuess
            # We don't need an else; in that case, testResult == 0, we've found our IV, and the loop will exit.
            '''
            # Note: This was the code from StackOverflow that I used to verify the correctness of the above code.
            # This also doesn't seem to work with too high an initial guess.
            estimatedPrice = me.bs.priceOption(type, sigmaGuess, yte, S, K, r)
            vega = me.getBSVega(S, K, yte, r, sigmaGuess)
            diff = currentPrice - estimatedPrice
            prevSigmaGuess = sigmaGuess
            sigmaGuess = sigmaGuess + diff/vega
            testResult = diff
            if prevSigmaGuess == sigmaGuess:
                break
            '''
            iterations += 1
        #print(f"IV found in {iterations} iterations.")
        return round(sigmaGuess,5)

    def getBSVega(me, S, K, T, r, sigma):
        # This is part of the code from StackOverflow that I used to verify the correctness of the above code.
        # The rest is commented out with a note above.
        d1 = ((np.log(S/K) + (r + 0.5 * sigma**2))*T)/(sigma * np.sqrt(T))
        return S*scipy.stats.norm.pdf(d1)* np.sqrt(T)


if __name__ == "__main__":
    ''' Test implementation. '''
    bsm = BlackScholesMerton()
    S = 50
    K = 45
    sigma = .3
    r = .02
    yte = 80/365 # Or should this be trading days (e.g., 250-256)?

    optionValue = bsm.priceOption('C', sigma, yte, S, K, r)
    print(f"Calculated option value: {optionValue}")

    brf = BSMRootFinder()
    calculatedIV = brf.getBSIV(optionValue, 'C', yte, S, K, r)
    print(f"Calculated IV: {calculatedIV*100}% (Actual: {sigma*100})%")

    optionValue = 44.4
    S = 179.495
    K = 135
    yte = 0.0136986
    r = .0028
    calculatedIV = brf.getBSIV(optionValue, 'C', yte, S, K, r)
    print(f"Calculated IV: {calculatedIV * 100}% (Actual: ?)")
    sigma = .35 #calculatedIV
    optionValue = bsm.priceOption('C', sigma, yte, S, K, r)
    print(f"Calculated option value: {optionValue}")
