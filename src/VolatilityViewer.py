import numpy as np
from matplotlib import ticker
import matplotlib.pyplot as plot


class VolatilityViewer:

    '''
    Andrew W.E. McDonald, 2021-12-12
    '''

    def __init__(me, daysToExpiry: [int,], strikes: [float,], impliedVols: np.array):
        '''
        Plots a 3D volatility surface.
        :param daysToExpiry: must be length n
        :param strikes: must be length n
        :param impliedVols: n x n numpy array, rows are strikes, columns are expiries
        '''
        me.expiries = np.asarray(daysToExpiry)
        me.strikes = np.asarray(strikes)
        me.impliedVols = impliedVols * 100 # change to percent
        #print(me.expiries)
        #print(me.strikes)

        me.plotIV()
        #me.runTest()

    def plotIV(me):
        xs, ys = np.meshgrid(me.expiries, me.strikes)
        fig = plot.figure(figsize=(24, 16))
        axes = fig.gca(projection='3d')
        axes.w_xaxis.set_major_locator(ticker.FixedLocator(me.expiries))
        plot.rc('axes', labelsize=12)
        axes.set_xlabel("Time to Expiry (days)", fontsize=16)
        axes.set_ylabel("K (USD)", fontsize=16)
        axes.set_zlabel("Annual IV (%)", fontsize=16)
        axes.set_title("AAPL Call Option Implied Volatility as of 2021-12-10 (r=0.28%, 1 year T-Bill)", fontsize=20)
        axes.dist = 9 # Sets camera zoom
        # Pad the color range by 10% in each direction.
        # Actually, don't.
        #minVol = np.min(me.impliedVols) * .9
        #maxVol = np.max(me.impliedVols) * 1.1
        #surface = axes.plot_surface(xs, ys, me.impliedVols, cmap=plot.cm.viridis, linewidth=0.2, vmin=minVol, vmax=maxVol)  # Order is X, Y, Z
        surface = axes.plot_surface(xs, ys, me.impliedVols, cmap=plot.cm.viridis, linewidth=0.2)  # Order is X, Y, Z
        plot.colorbar(surface, shrink=0.2, aspect=10, label="Annual IV (%)")

        plot.show()



    def runTest(me):
        '''
        a = np.arange(-1, 1, 0.02)
        b = a
        a, b = np.meshgrid(a, b)
        fig = plot.figure()
        axes = fig.gca(projection='3d')
        axes.plot_surface(a, b, a ** 2 + b ** 2,cmap=plot.cm.viridis, linewidth=0.2) # Order is X, Y, Z
        plot.show()
        '''
        a, b = np.meshgrid(me.expiries, me.strikes)
        vols = a ** 2 + b ** 2
        fig = plot.figure(figsize=(24, 16))
        axes = fig.gca(projection='3d')
        axes.w_xaxis.set_major_locator(ticker.FixedLocator(me.expiries))
        surface = axes.plot_surface(a, b, vols, cmap=plot.cm.viridis, linewidth=0.2)  # Order is X, Y, Z
        fig.colorbar(surface, shrink=0.5, aspect=10)
        plot.show()