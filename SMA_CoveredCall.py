from AlgorithmImports import *
from datetime import timedelta



class ScheduleSetHoldingsOnCloseSellOpen(QCAlgorithm):
    def Initialize(self):
        # set start and end date for backtest
        self.SetStartDate(2021, 1, 1)
        self.SetEndDate(2022, 12, 31)

        # initialize cash balance
        self.SetCash(1000000)
        
        # add an equity
        self.equity = self.AddEquity("AAPL")
        option = self.AddOption("AAPL") 
        self.symbol = option.Symbol
        
        #set strike/expiry filter for this option chain
        option.SetFilter(-3, 3, 0, 30)
        
        #use the underlying equity as the benchmark
        self.SetBenchmark(self.equity.Symbol)
        
        # benchmark against S&P 500
        self.SetBenchmark("SPY")
        
        self.sma = self.SMA(self.equity.Symbol, 20)
        
        #schedule a function to run every day just after market opens
        self.Schedule.On(self.DateRules.EveryDay(self.equity.Symbol), self.TimeRules.AfterMarketOpen(self.equity.Symbol, 1), self.CheckMovingAverage)
            
    def CheckMovingAverage(self):
        movingaverage = self.sma.Current.Value
        if self.equity.Price > movingaverage:
            return 1
        return -1
    
    
    def OnData(self, slice):
        if self.CheckMovingAverage() > 0:
            if not self.Portfolio[self.symbol.Underlying].Invested:
                #buy 100 shares of underlying stocks
                self.MarketOrder(self.symbol.Underlying, 100)
                
            chain = slice.OptionChains.get(self.symbol)
            if not chain:
                return
            
            if any([x for x in self.Portfolio.Values if x.Invested and x.Type == SecurityType.Option]):
                return
            
            calls = [x for x in chain if x.Right == OptionRight.Call]
            if not calls:
                return
            
            #sorted the contracts according to their expiration dates and choose the ATM options
            calls = sorted(sorted(calls, key=lambda x: abs(chain.Underlying.Price - x.Strike)), key =  lambda x: x.Expiry, reverse=True)
            
            #short the call options
            self.MarketOrder(calls[0].Symbol, 1)
            
    def OnOrderEvent(self, orderEvent):
        self.Log(f'{orderEvent}')
