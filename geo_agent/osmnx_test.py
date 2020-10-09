import osmnx as ox
import timeit

ox.config(
    log_console=True,
    log_file=True,
    use_cache=True,
    data_folder=".temp/data",
    logs_folder=".temp/logs",
    imgs_folder=".temp/imgs",
    cache_folder=".temp/cache",
)
def test_nearest():
    res =ox.pois.pois_from_point((51.66176239080847, -0.1687473308241547), tags={'shop':'supermarket'}, dist=3000)
    return res


if __name__ == '__main__':
    import timeit
    print(timeit.timeit("test_nearest()", setup="from __main__ import test_nearest", number=1))