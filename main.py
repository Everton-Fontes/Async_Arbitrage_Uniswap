from arbitrage import Uniswap_arb
import asyncio


async def main():
    bot = Uniswap_arb(1, 5)  # Value To trade | Percentage Calc | FEE

    # retrieve data from uniswap and convert to object
    await bot._set_pairs()

    # load all triangles
    # setting all combinations of pairs (first 500 pairs)
    # it take a while if the first time, after get fast
    await bot.load_triangules()

    # get info from uniswap
    info = await bot.info()

    # update prices for all triangles
    await bot.set_triangular_prices(info)

    # calculate all triangles
    triangles = await bot._calc_surface()

    # describe all triangules
    for triangule in triangles:
        await bot.describe_triangle(triangule)

if __name__ == "__main__":
    asyncio.run(main())
