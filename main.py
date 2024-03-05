from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
from hyperliquid.utils import constants
from datetime import datetime , timedelta
from discord_webhook import DiscordWebhook, DiscordEmbed
import time
import eth_account
import traceback
import json
import logging


logging.basicConfig(filename='botTrend.log', level=logging.INFO,format='%(asctime)s:%(levelname)s:%(message)s')

class TrendFollowing:
    def __init__(self):
        self.config = json.load(open("config.json"))
        self.wallet =  eth_account.Account.from_key(self.config["privateKey"])
        self.exchangeHpl = Exchange(self.wallet, constants.MAINNET_API_URL)
        self.infoHpl = Info()
        self.webhook = DiscordWebhook(url=self.config["webhookUrl"])
        self.sizeUsd = self.config["sizeUSD"]
        self.maxOpenPositions = self.config["maxOpenPositions"]
        self.numberOfCoins = self.config["numberOfCoins"]
        self.leverage = self.config["leverage"]
        self.symbolList = []
        self.activePositions = []

    def get20DayHigh(self,coin : str) -> tuple:
        price_data = self.fetchPriceData(coin, 19, "1d")
        twenty_day_high = max(price_data) 
        return twenty_day_high, price_data
      
    def fetchPriceData(self,coin : str ,dayBack : int,interval : str) -> list:
        startTimestampMs = datetime.now() - timedelta(days=dayBack)
        endTimestampMs = datetime.now()
        coinData = self.infoHpl.candles_snapshot(coin, interval, int(startTimestampMs.timestamp()) * 1000, int(endTimestampMs.timestamp()) * 1000)
        priceData = [float(data["c"]) for data in coinData]
        return priceData
    
    def checkAthDay(self,coin : str) -> int:
        twenty_day_high, price_data = self.get20DayHigh(coin)

        price_data.reverse()
        # Check if the current price is within 5 days of the 20-day high
        index_twenty_day_high = price_data.index(twenty_day_high)
        if index_twenty_day_high == 0:
            return 0
        elif index_twenty_day_high <= 3:
            return 1
        elif index_twenty_day_high >= 4 and index_twenty_day_high < 14:
            return 2
        elif index_twenty_day_high == 14:
            return 3
        elif index_twenty_day_high >= 15 and index_twenty_day_high < 19:
            return 4
        else:
            return 5

    def updateLeverage(self,coin : str,leverage : int) -> None:
        self.exchangeHpl.update_leverage(leverage=leverage, coin=coin)
        logging.info(f"Leverage updated to {leverage} for {coin}")

    def getTopCoins(self) -> None:
        coins = self.infoHpl.post("/info", {"type": "metaAndAssetCtxs"})
        topCoins = []
        for i in range(len(coins[0]["universe"])):
            topCoins.append({
                "coin":coins[0]["universe"][i]["name"],
                "volume":float(coins[1][i]["dayNtlVlm"])
            })
        topCoins = sorted(topCoins, key=lambda x: x["volume"], reverse=True)
        self.symbolList = [x["coin"] for x in topCoins[:self.numberOfCoins]]

    def getLotSize(self,coin: str) -> float:
        res = self.infoHpl.meta()
        coinData = [x for x in res["universe"] if x["name"] == coin]
        return coinData[0]["szDecimals"]

    def getLatestPrice(self,coin: str,is_buy: bool,slippage: float):
        # Get midprice
        px = float(self.infoHpl.all_mids()[coin])
        # Calculate Slippage
        px *= (1 + slippage) if is_buy else (1 - slippage)
        # We round px to 5 significant figures and 6 decimals
        return round(float(f"{px:.5g}"), 6)
        
    def sendError(self,error : str) -> None:
        embed = DiscordEmbed(title="Trend Hyperliquid", description=error, color=15400960)
        self.webhook.add_embed(embed)
        self.webhook.execute()
        self.webhook.remove_embeds()

    def sendMsg(self,msg : str) -> None:
        embed = DiscordEmbed(title="Trend Hyperliquid", description=msg, color=65454)
        self.webhook.add_embed(embed)
        self.webhook.execute()
        self.webhook.remove_embeds()
    
    def sendOrder(self,open : bool,side : bool,coin : str,closeSz : int = 0) -> None:
        try:
            price = self.getLatestPrice(coin, side, 0.01)
            sz = self.sizeUsd / price
            sz = round(sz,self.getLotSize(coin))
            if open:
                r = self.exchangeHpl.order(
                    coin, side, sz,price,{"limit": {"tif": "Ioc"}}
                )
            else:
                r = self.exchangeHpl.order(
                    coin, side, closeSz,price,{"limit": {"tif": "Ioc"}}
                )
            logging.info(f"Order : {r} on {coin} at {price}")
            if r["response"]["data"]["statuses"][0]:
                if 'filled' in r["response"]["data"]["statuses"][0]:
                    return price , sz
            else:
                self.sendError(f"Error in {coin} \nOrder : {r}")

        except :
            self.sendError(traceback.format_exc())
            
    def getActivePosition(self) -> None:
        result = self.infoHpl.user_state(self.exchangeHpl.wallet.address)
        positionList = []
        for position in result["assetPositions"]:
            positionList.append({
                "symbol":position["position"]["coin"],
                "size":abs(float(position["position"]["szi"])),
                "side": True if float(position["position"]["szi"]) > 0 else False
            })
        self.activePositions = positionList
    
    def rebalance(self) -> None:
        self.sendMsg("Rebalance Started")
        # get Data
        self.getTopCoins()
        self.getActivePosition()

        # rebalance active positions

        for coin in self.activePositions:
            athDays = self.checkAthDay(coin["symbol"])
            if coin["side"]:
                if athDays == 0:
                    logging.info(f"New high keep : {coin['symbol']} position")
                    continue
                elif athDays == 1:
                    logging.info(f"Range keep : {coin['symbol']} position")
                    continue
                else:
                    logging.info(f"Close long : {coin['symbol']} position")
                    self.sendOrder(False, False, coin["symbol"], coin["size"])
                    self.sendMsg(f"Closed long : {coin['symbol']} position")
                    time.sleep(1)
            else:
                if athDays == 3:
                    logging.info(f"keep : {coin['symbol']} position")
                    continue
                elif athDays == 4:
                    logging.info(f"Range keep : {coin['symbol']} position")
                    continue
                else:
                    logging.info(f"Close short {coin['symbol']} position")
                    self.sendOrder(False, True, coin["symbol"], coin["size"])
                    self.sendMsg(f"Closed short : {coin['symbol']} position")
                    time.sleep(1)
        
        # open new positions
                
        for coin in self.symbolList:
            athDays = self.checkAthDay(coin)
            if athDays == 0:
                if coin not in [x["symbol"] for x in self.activePositions] and len(self.activePositions) < self.maxOpenPositions:
                    self.updateLeverage(coin, self.leverage)
                    logging.info(f"Open long : {coin} position")
                    self.sendOrder(True, True, coin, 0)
                    self.sendMsg(f"Opened long : {coin} position")
                    time.sleep(2)
                else:
                    logging.info(f"Position already open for {coin} or max open positions reached")
                    continue
            if athDays == 3:
                if coin not in [x["symbol"] for x in self.activePositions] and len(self.activePositions) < self.maxOpenPositions:
                    self.updateLeverage(coin, self.leverage)
                    logging.info(f"Open short : {coin} position")
                    self.sendOrder(True, False, coin, 0)
                    self.sendMsg(f"Opened short : {coin} position")
                    time.sleep(2)
            else:
                continue

        # rebalance done
        self.sendMsg("Rebalance Done")

    def run(self) -> None:
        self.sendMsg("Started Trend")
        while True:
            self.rebalance()
            time.sleep(60*60*24)

trend = TrendFollowing()
trend.run()