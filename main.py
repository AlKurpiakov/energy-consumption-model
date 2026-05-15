import argparse
from typing import List, Dict
import heapq
import math

# при реализации были выбраны SoA структуры вместо использования массивов  
# структур, потому что при большом кол-ве потребителей и генераторов
# будет улучшено расположение структур в памяти и повысится скорость выполнения кода

# Структуры данных
class Consumers:
    __slots__ = ("ids", "demand")

    def __init__(self, ids: List[str],  demand: List[List[float]]):
        self.ids = ids
        self.demand = demand


class SolarGeneratos:
    __slots__ = ("ids", "profile", "cost_per_kwh")

    def __init__(self, ids: List[str], profile: List[List[float]], cost_per_kwh: List[float]):
        self.ids = ids
        self.profile = profile
        self.cost_per_kwh = cost_per_kwh


class DieselGeneratos:
    __slots__ = ("ids", "power", "cost_per_kwh")

    def __init__(self, ids: List[str], power: List[float], cost_per_kwh: List[float]):
        self.ids = ids
        self.power = power
        self.cost_per_kwh = cost_per_kwh

# Вспомогательные Функции 
def pick_best_diesels_dp(diesels: DieselGeneratos, needed_power: float):
    if needed_power <= 0:
        return [], 0.0
    n = len(diesels.ids)
    if n == 0:
        return [], float("inf")

    max_power = sum(diesels.power)
    step = 0.1

    size = math.ceil(max_power / step) + 1
    req = math.ceil(needed_power / step)

    INF = float("inf")
    dp = [INF] * size
    prev = [None] * size
    dp[0] = 0.0

    for i in range(n):
        p = math.ceil(diesels.power[i] / step)
        cost = diesels.power[i] * diesels.cost_per_kwh[i]
        for cur in range(size - 1 - p, -1, -1):
            if dp[cur] == INF:
                continue
            new_p = cur + p
            new_cost = dp[cur] + cost
            if new_cost < dp[new_p]:
                dp[new_p] = new_cost
                prev[new_p] = (cur, i)

    best_p = None
    best_cost = INF
    for p in range(req, size):
        if dp[p] < best_cost:
            best_cost = dp[p]
            best_p = p

    if best_p is None:
        return [], float("inf")

    chosen_idx = []
    p = best_p
    while p != 0:
        step_info = prev[p]
        if step_info is None:
            break
        prev_p, idx = step_info
        chosen_idx.append(idx)
        p = prev_p

    chosen_ids = [diesels.ids[i] for i in chosen_idx]
    return chosen_ids, best_cost


def simulate(consumers: Consumers, solar: SolarGeneratos, diesel: DieselGeneratos) -> None:
    hours = list(range(1, 25))

    solar_total_by_hour = [0.0] * 24
    solar_cost_by_hour = [0.0] * 24
    solar_on_by_hour = [[] for _ in range(24)]

    for h in hours:
        total = 0.0
        cost = 0.0
        on = []
        for i in range(len(solar.ids)):
            gen = solar.profile[i][h - 1]
            if gen > 0:
                on.append(solar.ids[i])
            total += gen
            cost += gen * solar.cost_per_kwh[i]
        solar_total_by_hour[h - 1] = total
        solar_cost_by_hour[h - 1] = cost
        solar_on_by_hour[h - 1] = on

    demand_total_by_hour = [0.0] * 24
    for h in hours:
        demand_total_by_hour[h - 1] = sum(consumers.demand[i][h - 1] for i in range(len(consumers.ids)))

    max_diesel_power = sum(diesel.power)

    print("Час\tСтоимость\tСолнечные\tДизели\tОтключённые")
    for h in hours:
        solar_total_gen = solar_total_by_hour[h - 1]
        solar_cost = solar_cost_by_hour[h - 1]

        max_total_gen = solar_total_gen + max_diesel_power
        demand_total = demand_total_by_hour[h - 1]

        if max_total_gen < demand_total:
            heap = [(consumers.demand[i][h - 1], i) for i in range(len(consumers.ids))]
            heapq.heapify(heap)

            selected = []
            sum_sel = 0.0
            while heap:
                d, idx = heapq.heappop(heap)
                if sum_sel + d <= max_total_gen:
                    selected.append(idx)
                    sum_sel += d
                else:
                    break

            consumers_off = [i for i in range(len(consumers.ids)) if i not in selected]
            actual_demand = sum_sel
        else:
            consumers_off = []
            actual_demand = demand_total

        R = actual_demand - solar_total_gen
        if R <= 0:
            diesel_used = []
            diesel_cost = 0.0
        else:
            diesel_used, diesel_cost = pick_best_diesels_dp(diesel, R)

        total_cost = solar_cost + diesel_cost
        off_names = [consumers.ids[i] for i in consumers_off]
        solar_names = solar_on_by_hour[h - 1]

        print(f"{h:2d}\t{total_cost:7.2f}\t{solar_names}\t{diesel_used}\t{off_names}")


# Тесты
def test_case_excess():
    print("\n=== Тест 1: Избыток генерации ===")
    consumers = Consumers(
        ids=[f"{i}" for i in range(1, 11)],
        demand=[
            [
                0.3, 0.2, 0.2, 0.2, 0.2, 0.3, 0.4, 0.5, 0.6, 0.6,
                0.5, 0.5, 0.4, 0.4, 0.5, 0.6, 0.7, 0.7, 0.7, 0.6,
                0.5, 0.4, 0.4, 0.3
            ] for _ in range(10)
        ]
    )

    solar = SolarGeneratos(
        ids=["SolarPanel1", "SolarPanel2"],
        profile=[
            [
                0.0,0.0,0.0,0.0,0.0,0.1,0.5,1.0,1.8,2.5,
                3.0,3.5,4.0,4.5,4.0,3.0,2.0,1.0,0.5,0.1,
                0.0,0.0,0.0,0.0
            ],
            [
                0.0,0.0,0.0,0.0,0.0,0.0,0.2,0.8,1.5,2.2,
                2.8,3.2,3.5,3.8,3.5,2.5,1.5,0.7,0.2,0.0,
                0.0,0.0,0.0,0.0
            ],
        ],
        cost_per_kwh=[0.1, 0.1]
    )

    diesel = DieselGeneratos(
        ids=["DieselEngine1", "DieselEngine2"],
        power=[5.0, 3.0],
        cost_per_kwh=[1.0, 1.2]
    )

    simulate(consumers, solar, diesel)

def test_case_deficit():
    print("\n=== Тест 2: Дефицит энергии ===")
    consumers = Consumers(
        ids=[f"{i}" for i in range(1, 11)],
        demand=[
            [
                0.5, 0.3, 0.2, 0.2, 0.2, 0.3, 0.4, 0.6, 0.8, 0.7,
                0.6, 0.5, 0.4, 0.4, 0.5, 0.9, 1.5, 2.0, 2.5, 2.2,
                1.5, 1.0, 0.9, 0.7
            ] for _ in range(10)
        ]
    )

    solar = SolarGeneratos(
        ids=["SolarPanel1", "SolarPanel2"],
        profile=[
            [
                0.0,0.0,0.0,0.0,0.0,0.0,0.1,0.2,0.5,0.8,
                1.0,1.2,1.5,1.5,1.3,0.9,0.5,0.2,0.1,0.0,
                0.0,0.0,0.0,0.0
            ],
            [
                0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.1,0.3,0.6,
                0.9,1.0,1.2,1.3,1.2,0.8,0.4,0.1,0.0,0.0,
                0.0,0.0,0.0,0.0
            ],
        ],
        cost_per_kwh=[0.1, 0.1]
    )

    diesel = DieselGeneratos(
        ids=["DieselEngine1"],
        power=[6.0],
        cost_per_kwh=[1.0]
    )

    simulate(consumers, solar, diesel)


TESTS: Dict[str, callable] = {
    "excess": test_case_excess,
    "deficit": test_case_deficit,
    "all": lambda: (test_case_excess(), test_case_deficit()),
}


def main():
    parser = argparse.ArgumentParser(description="Симулятор энергосети")
    parser.add_argument(
        "-t", "--test",
        default="all",
        choices=TESTS.keys(),
        help="Тип запускаемого теста: excess, deficit, all"
    )
    args = parser.parse_args()
    TESTS[args.test]()


if __name__ == "__main__":
    main()