import asyncio
from arbitrage.pairs import *
from arbitrage import factory
from connection import Uniswap_GraphQL
from uniswap import Uniswap
from web3 import Web3


class _Uniswap:
    def __init__(self, address: str, private_key: str, provider: str) -> None:
        self.__my_address = address
        self.__private_key = private_key
        self.__provider = provider
        self.swapper = Uniswap(address=self.my_address,
                               private_key=self.private_key, version=3, provider=provider)
        self.eth = Web3.toChecksumAddress(
            "0x0000000000000000000000000000000000000000")

    @property
    def my_address(self) -> str:
        return self.__my_address

    @property
    def private_key(self) -> str:
        return self.__private_key

    @property
    def provider(self) -> str:
        return self.__provider

    async def _get_ask_bid(self, pair: Pair):
        base_rate = self.swapper.get_price_output(
            Web3.toChecksumAddress(pair.base.address),
            Web3.toChecksumAddress(pair.quote.address), pair.quote.wei, pair.fee)
        quote_rate = self.swapper.get_price_output(
            Web3.toChecksumAddress(pair.quote.address),
            Web3.toChecksumAddress(pair.base.address), pair.base.wei, pair.fee)

        bid = 1/base_rate*pair.base.wei
        ask = 1/quote_rate*pair.quote.wei
        await pair.set_all_asks_bids(ask, bid)

    async def _buy_base_pair(self, pair: Pair, amount: float):
        self.swapper.make_trade(self.eth,
                                Web3.toChecksumAddress(pair.base.address),
                                amount*10**18)  # sell 1 ETH for BASE

    async def _sell_token_pair(self, pair: Pair, amount: float, token='BASE'):
        if token == 'quote':
            token_buy = Web3.toChecksumAddress(pair.base.address)
            token_sell = Web3.toChecksumAddress(pair.quote.address)
            wei = pair.quote.wei
        else:
            token_buy = Web3.toChecksumAddress(pair.quote.address)
            token_sell = Web3.toChecksumAddress(pair.base.address)
            wei = pair.base.wei

        # make Trade
        self.swapper.make_trade(token_buy, token_sell,
                                amount*wei)  # buy ETH for 1 BAT

    async def _sell_crypto(self, token: Crypto, amount: float):
        sell_token = Web3.toChecksumAddress(token.address)
        self.swapper.make_trade(sell_token, amount*token.wei)


class Uniswap_arb(factory.Factory_Arbitrage):

    def __init__(self, initial_value: float, perc: float, fee: float = (1-0.00075)) -> None:
        super().__init__(initial_value, fee, perc)
        self.conn = Uniswap_GraphQL()

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
                             quote=quote, address=pair['id'], fee=pair['feeTier'])
            self.add_pairs(pair_inst)

    async def _set_pairs(self):
        info = await self.info()
        for pair in info:
            base = Crypto(symbol=pair['token0']
                          ['symbol'], address=pair['token0']['id'], decimals=int(pair['token0']['decimals']), dec_price=pair['token0Price'])

            quote = Crypto(symbol=pair['token1']
                           ['symbol'], address=pair['token1']['id'], decimals=int(pair['token1']['decimals']), dec_price=pair['token1Price'])

            pair_inst = Pair(pair='', base=base,
                             quote=quote, address=pair['id'], fee=pair['feeTier'])

            await self._add_pairs(pair_inst)

    async def set_pair_ask_bid(self, info: dict, pair: Pair):
        inf = [inf for inf in info if inf['id'] == pair.address]
        if inf:
            bid = pair.base.set_price(round(float(
                inf[0]['token0Price']), 8))
            ask = pair.quote.set_price(round(float(
                inf[0]['token1Price']), 8))
            await pair.set_all_asks_bids(ask, bid)

    async def uniswap_calc(self, con: _Uniswap) -> None:
        res = await asyncio.gather(*[asyncio.create_task(self.update_ask_uniswap(con, tri)) for tri in await self.triangular_pair_list()])
        for triangle in res:
            self.describe_triangle(triangle)

    async def update_ask_uniswap(self, con: _Uniswap, triangle: Triangles_pair):
        try:
            await asyncio.gather(*[asyncio.create_task(con._get_ask_bid(pair)) for pair in triangle.pair_list])
            return triangle
        except:
            self.__triangular_pair_list.remove(triangle)
            return
