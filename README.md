# Hyperliquid-Basic-Trend

This is a basic trend following strategy. the strategy itself is very dumb and simple, but it is a good starting point for trend following strategies.

## Getting Started

You can run the strategy in a few different ways. You can run it in a docker container, or you can run it locally.

### Prerequisites

* You need to have a account on the Hyperliquid platform. You can create an account [here](https://app.hyperliquid.xyz/join/ONK). ("referral link who give 4% discount on trading fees").
* You will need a discord webhook url to get notifications from the strategy. You can create a webhook url by following [this guide](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks).
* Complete the config.json file with your credentials and the webhook url.
* The min open size is 10 USD.
* you need at minimum to have a balance superior to size / leverage *  max open positions
* keep in mind that you can be liquidated if you use leverage and dont have enough balance to support the position.


### Docker

```bash 
sudo docker build -t hyperliquid-trend .
sudo docker run -d hyperliquid-trend
```

### Local

* Need to have python 3.10.11 installed.

```bash
pip install hyperliquid-python-sdk discord_webhook
python main.py
```

## Strategy

### Explanation

* The strategy is very simpe it get the last 20 closing days price.
* If today's is the highest price in the last 20 days, it will open a long.
* If it's been 5 days without a new high, it will close the long.
* If it's been 15 days without a new high, it will open a short.
* If it's been 20 days without a new high, it will close the short.
* The universe is the top X coins by volume in hyperliquid.
* You can change the number of coins in the config.json file.
* You can also change the leverage and the number of max open positions simultaneously.

### Disclaimer

* This is a basic trend following strategy, it is not a financial advice.
* You can lose all your money using this strategy.
* Use it at your own risk.


## Contributions

* If you want to contribute to the project, you can open a pull request.

* If you have any questions or suggestions regarding the repo, or just want to have a chat you can contact me below:

Twitter: [@kalypso_442](https://twitter.com/kalypso_442) : Discord: kalypso42

