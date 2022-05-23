from arbitrage.pairs import *
from arbitrage import factory
from connection import Uniswap


class Uniswap_arb(factory.Factory_Arbitrage):

    def __init__(self, initial_value: float, perc: float, fee: float = (1-0.00075)) -> None:
        super().__init__(initial_value, fee, perc)
        self.conn = Uniswap()

    async def info(self):
        info = await self.conn.retrieve_info()
        return info

    def set_pairs(self, info: list):
        for pair in info:
            base = Crypto(symbol=pair['token0']
                          ['symbol'], address=pair['token0']['id'], decimals=int(pair['token0']['decimals']), dec_price=pair['token0Price'])
            quote = Crypto(symbol=pair['token1']
                           ['symbol'], address=pair['token1']['id'], decimals=int(pair['token1']['decimals']), dec_price=pair['token1Price'])
            pair_inst = Pair(pair='', base=base,
                             quote=quote, address=pair['id'])
            self.add_pairs(pair_inst)

    async def _set_pairs(self):
        info = await self.info()
        for pair in info:
            base = Crypto(symbol=pair['token0']
                          ['symbol'], address=pair['token0']['id'], decimals=int(pair['token0']['decimals']), dec_price=pair['token0Price'])

            quote = Crypto(symbol=pair['token1']
                           ['symbol'], address=pair['token1']['id'], decimals=int(pair['token1']['decimals']), dec_price=pair['token1Price'])

            pair_inst = Pair(pair='', base=base,
                             quote=quote, address=pair['id'])

            await self._add_pairs(pair_inst)

    async def set_pair_ask_bid(self, info: dict, pair: Pair):
        inf = [inf for inf in info if inf['id'] == pair.address]
        if inf:
            bid = pair.base.set_price(float(
                inf[0]['token0Price']))
            ask = pair.quote.set_price(float(inf[0]['token1Price']))
            await pair.set_all_asks_bids(ask, bid)
