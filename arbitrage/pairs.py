def wrap_instance(v):
    if type(v) == Pair or type(v) == Crypto:
        v = vars(v)
        for key, var in v.items():
            if type(var) == Crypto:
                var = vars(var)
            v[key] = var
    return v


def unwrap_triangule(json_dict: dict):
    for k, v in json_dict.items():
        if type(v) == dict:
            base = Crypto(v['base']['symbol'], v['base']
                          ['address'], v['base']['decimals'])
            quote = Crypto(v['quote']['symbol'], v['quote']
                           ['address'], v['quote']['decimals'])
            p = Pair(pair='', base=base, quote=quote,
                     address=v['address'])
            v = p
        json_dict[k] = v

    return Triangles_pair(json_dict['pair_a'], json_dict['pair_b'], json_dict['pair_c'])


class Crypto:
    def __init__(self, symbol: str, address: str = '', decimals: int = 8, dec_price: float = 0) -> None:
        self.__symbol = symbol
        self.__price = dec_price
        self.__address = address
        self.__decimals = int(decimals)

    @property
    def symbol(self) -> str:
        return self.__symbol

    @property
    def address(self) -> str:
        return self.__address

    @property
    def price(self) -> float:
        return self.__price

    @property
    def decimals(self) -> int:
        return self.__decimals

    def set_price(self, ask: float) -> float:
        self.__price = ask
        return self.__price


class Pair:
    def __init__(self, pair: str, base: Crypto = None, quote: Crypto = None, address: str = '') -> None:
        self.__base = base
        self.__quote = quote
        if not self.base or not self.quote:
            self.set_cryptos(pair)
        self.__pair = f'{self.base.symbol}_{self.quote.symbol}'
        self.__ask = 0
        self.__bid = 0
        self.__address = address

    @property
    def pair(self) -> str:
        return self.__pair

    @property
    def address(self) -> str:
        return self.__address

    @property
    def base(self) -> Crypto:
        return self.__base

    @property
    def quote(self) -> Crypto:
        return self.__quote

    @property
    def ask(self):
        return self.__ask

    @property
    def bid(self):
        return self.__bid

    def set_cryptos(self, pair: str):
        pair = pair.split('_')
        self.__base = Crypto(pair[0])
        self.__quote = Crypto(pair[1])

    async def set_ask(self, ask: float) -> float:
        self.__ask = ask
        return self.ask

    async def set_bid(self, bid: float) -> float:
        self.__bid = bid
        return self.bid

    async def set_all_asks_bids(self, ask, bid):
        await self.set_ask(ask)
        await self.set_bid(bid)


class Triangles_pair:
    def __init__(self, pair_a: Pair, pair_b: Pair, pair_c: Pair) -> None:
        self.__pair_a = pair_a
        self.__pair_b = pair_b
        self.__pair_c = pair_c
        self.swap_1 = 0
        self.swap_2 = 0
        self.swap_3 = 0
        self.swap_1_rate = 0
        self.swap_2_rate = 0
        self.swap_3_rate = 0
        self.contract_1 = ''
        self.contract_2 = ''
        self.contract_3 = ''
        self.direction_trade_1 = ''
        self.direction_trade_2 = ''
        self.direction_trade_3 = ''
        self.acquired_coin_t1 = 0
        self.acquired_coin_t2 = 0
        self.acquired_coin_t3 = 0
        self.profit_loss_perc = 0
        self.profit_loss = 0
        self.direction = ''
        self.trade_description_1 = ''
        self.trade_description_2 = ''
        self.trade_description_3 = ''
        self.pair_list = [self.pair_a, self.pair_b, self.pair_c]
        self.__combined = f'{self.pair_a.pair},{self.pair_b.pair},{self.pair_c.pair}'

    @property
    def pair_a(self):
        return self.__pair_a

    @property
    def pair_b(self):
        return self.__pair_b

    @property
    def pair_c(self):
        return self.__pair_c

    @property
    def combined(self):
        return self.__combined

    async def set_all_asks_bids(self, asks: list, bids: list):
        assert len(asks) == len(self.pair_list)
        assert len(bids) == len(self.pair_list)

        for i, pair in enumerate(self.pair_list):
            await pair.set_all_asks_bids(asks[i], bids[i])

    def wrap_triangle(self):
        dictt = vars(self)
        for k, v in dictt.items():
            v = wrap_instance(v)
            if type(v) == list:
                v = [wrap_instance(item) for item in v]
            dictt[k] = v

        return dictt


if __name__ == "__main__":
    a = Pair('ETH_EOS')
    b = Pair('USDT_EOS')
    c = Pair('USDT_ETH')
    t = Triangles_pair(a, b, c)
