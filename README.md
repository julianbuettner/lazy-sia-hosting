# Lazy Sia Hosting

Automate the tasks that keep your Sia host running.

Intended for usage on Linux and with siad.

## Warning
1. Use at your own risk.  
2. I am not responsible for any losses of funds, data, or anything else.  
3. Always distrust anyone.

## What can I do with this?

This application helps you to automate tasks you regularily
have to perform on your Sia host.

You start your siad process first, then this application.

This application has multiple submodules.

On how to enable and configure these modules, see
[configuration](#Configuration).


### 📈 Automatic Pricing / 🥇 Ranking
The value of cryptographic currencies varies much, even
from hour to hour. So instead of adjusting the price
manually, you can use this submodule.

You have two options:

- _Eins_: go by Siacoin/USD
- _Zwei_: go by rank #123

And the second option is much more fun.  
Say you want to go for rank #45 on siastats.info.  
Then your price will adjust, so that you land on rank #45.  
If you then do other things to improve your rank, i.e.
reduce the bandwith price, or increase your uptime, you
will see your storage price go up, while keeping your rank.

Algorithm:  
- get rank delta, i.e. -5 (current #50, target #45)  
- new price = old price * 1.01 ^ (rank delta)  
- sleep  
- repeat  

_Warning_:
If your hosts goes offline for a long time, the price might
go to zero. So specify a minimum price in Siacoins
greater than zero.


### 🔄 Automatic Restart
Does your sia server sometimes crash?  
Well - mine does. Because it's a ~~potato~~ pi and one drive
had power issues.  
So you might want a restart routine in some cases.

You can specify an order of commands to shut down and to start, with an sleep inbetween.

The algorithm is:
- wait until the server seams to be down for a bit
- run the shutdown commands. example:
    - `sudo service siad stop`
- sleep for a few seconds
- run the start commands
    - `sudo mount -a`
    - `sudo service siad start`
- repeat

### 🔑 Automatic Unlock
[Propper way of doing it.](https://support.sia.tech/your-sia-wallet/for-advanced-users/how-to-automatically-restart-and-unlock-sia)


If you restart your server, the wallet is locked and
your host can not do much, because
it is missing it's private key.

So to avoid that, you can enable this submodule.

It checks every 10 seconds if your wallet is locked,
and if it is, it unlocks it.

For that you have to enter your password or seed phrase into the
config. So you want to be VERY sure noone can read it.  
Disable SSH password authentication, check file permissions,
etc.  
I also encourage you to read the code of this project
before doing this. Trust noone.

The algorithm is:  
- wait until the wallet is locked
- unlock the wallet
- repeat


### 💰 Automatic Payout
So, if you have automatic unlock enabled, you should
try to keep as little Siacoins as possible on the host,
and keep as much as possible on a safe wallet.

For this, this submodule exists.

You define a Payout block, and a a minimum of coins
to stay on the server.  
If you host together with a friend, as I do, you might want
to specify a block like this:
- 100 address-one
- 100 address-two
- 50 address-for-some-other-purpose

So the block size is 250 Siacoins.  
If you now set your minimum avaiable coin amount to
4000 Coins, at 4250 available, one block will be transfered.

Available means not locked, but freely available, confirmed balance.

Also consider the transaction fees.  
[siastats.info/transactions](https://siastats.info/transactions)

Algorithm:
- wait for available-minimum + blocksize to be available
- send the coins
- repeat

### 🎮 Automatic Throttling
If you host at home, have a shitty ISP and still want 
to be able to play online games, you might need to
throttle your sia server.  

My ISP can handle more traffic in the morning and less in
the evening, so a static rate didn't cut it for me.

Algorithm:
- do speedtest
- set throttling in relation to speed test results
- sleep


## Configuration
Your `config.yaml` has to be in the same directory as
`start.sh`.  
The config will be read and validated once at start.  

```yaml
host: 127.0.0.1:9980
api-password: hex-123-abc-456  # cat ~/.sia/apipassword

price:
    enabled: yes
    minimum-price: 25  # SC/TB/month
    # if storage price is 100SC, collateral is 250SC:
    collateral-factor: 2.5

    # either provide (a):
    usd: 1.234  # $/TB/month
    # or (b):
    siastats-rank: 45  # https://siastats.info/hosts
    # or (c):
    hostdb-rank: 45  # siac hostdb

restart:
    enabled: yes
    stop-commands:
        # This works only because I installed siad as a service
        - sudo service siad stop
    sleep: 123.4  # seconds
    start-commands:
        - sudo mount -a
        - sudo service siad start
    cooldown: 500  # seconds

unlock:
    enabled: yes
    wallet-password: password or seed be careful with it

payout:
    enabled: yes
    minimum-available: 4000  # SC
    block:
        # Do not forget the dash before name
      - name: wallet1
        address: abc-hex-123  # double check
        amount: 50  # SC

      - name: wallet2
        address: abc-hec-321  # double check
        amount: 100  # SC


throttle:
    enabled: yes
    interval: 1800  # seconds
    up: 0.4  # use 40% up maximum
    down: 0.8  # use 80% down maximum
    interface: eth0  # cat /sys/class/net/eth0/statistics/rx_bytes
    unthrottle-command:
        # Works only after installing wondershaper
        - sudo wondershaper -a {interface} -c
    throttle-command:
        - sudo wondershaper -a {interface} -u {kbits_up} -d {kbits_down}
        # cast as integers {m, k}{bits, bytes}_{up, down}

```


## Start
```bash
pip3 install -r requirements  # requests pyyaml
./start.sh
```

## Contributing
Any improvement ideas?  
Open an issue.

Want to contribute code?  
Open a pull request.

Found a bug?  
Open an issue.

You could also buy me a coffee (with Siacoins of course):  
`32f2345729a90728f880607d139eb457304505620ac748ffa5241e4953e4dc765c2f039c59f4` - Sia only
