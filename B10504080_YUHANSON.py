import matplotlib.pyplot as plt


load = [
    0.6, 0.5, 0.5, 0.5, 0.5, 0.6,
    1.2, 1.5, 1.0, 0.8, 0.7, 0.7,
    0.8, 0.7, 0.8, 0.9, 1.2, 1.8,
    2.5, 2.3, 2.0, 1.5, 1.0, 0.7
]

pv = [
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
    0.0, 0.2, 0.8, 1.5, 2.5, 3.2,
    3.5, 3.0, 2.2, 1.2, 0.5, 0.1,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0
]

price_buy = (
    [1.99] * 6 +
    [4.48] * 5 +
    [1.99] * 3 +
    [4.48] * 10
)

price_sell = [5.6279] * 24

BAT = {
    "E_max": 10.0,      "E_init": 5.0,
    "P_ch_max": 3.3,    "P_dis_max": 3.3,
    "eta_ch": 0.95,     "eta_dis": 0.95
}

DT = 1.0  # hour



def simulate(strategy_name, bat_params):
    # NameError 방지를 위한 변수 정의
    E = bat_params["E_init"]
    E_max = bat_params["E_max"]
    P_ch_max = bat_params["P_ch_max"]
    P_dis_max = bat_params["P_dis_max"]
    eta_ch = bat_params["eta_ch"]
    eta_dis = bat_params["eta_dis"]

    soc_history = []
    grid_buy_history = []
    grid_sell_history = []
    cost_history = []

    total_cost = 0.0
    total_buy_kwh = 0.0
    total_sell_kwh = 0.0

    for t in range(24):
        P_pv = pv[t]
        P_load = load[t]
        net_load = P_load - P_pv  # (+) deficit, (-) surplus

        P_ch = 0.0
        P_dis = 0.0
        P_grid = 0.0  # (+) buy, (-) sell

        #  Strategy A: Self-Consumption 
        if strategy_name == "A_Self_Consumption":
            if net_load < 0:  
                surplus = -net_load
                P_ch = min(surplus,
                           P_ch_max,
                           (E_max - E) / eta_ch)
                P_sell = surplus - P_ch
                P_grid = -P_sell
            else:  
                deficit = net_load
                P_dis = min(deficit,
                            P_dis_max,
                            E * eta_dis)
                P_grid = deficit - P_dis

        # Strategy B: Price-Based (safe version, no battery export)
        elif strategy_name == "B_Price_Optimized":
            curr_price = price_buy[t]

            if curr_price < 2.5:
                P_dis = 0.0
                P_ch = min(P_ch_max, (E_max - E) / eta_ch)
                # Energy balance: P_grid + P_pv - P_ch - P_load = 0
                P_grid = P_load + P_ch - P_pv

            elif curr_price > 4.0 and net_load > 0:
                P_ch = 0.0
                deficit = net_load
                P_dis = min(deficit, P_dis_max, E * eta_dis)
                P_grid = deficit - P_dis

            else: # Normal -> same as Strategy A
                if net_load < 0:
                    surplus = -net_load
                    P_ch = min(surplus, P_ch_max, (E_max - E) / eta_ch)
                    P_grid = -(surplus - P_ch)
                else:
                    deficit = net_load
                    P_dis = min(deficit, P_dis_max, E * eta_dis)
                    P_grid = deficit - P_dis
        else:
            raise ValueError("Unknown strategy_name")

        # Battery update (difference equation)
        E_next = E + (eta_ch * P_ch - P_dis / eta_dis) * DT
        E_next = max(0.0, min(E_max, E_next))

        # Cost
        if P_grid > 0:  # Buying
            step_cost = P_grid * price_buy[t] * DT
            total_buy_kwh += P_grid * DT
            grid_buy_history.append(P_grid)
            grid_sell_history.append(0.0)
        else:  # Selling
            step_cost = P_grid * price_sell[t] * DT  
            total_sell_kwh += (-P_grid) * DT
            grid_buy_history.append(0.0)
            grid_sell_history.append(-P_grid)

        total_cost += step_cost

        soc_history.append(E_next)
        cost_history.append(total_cost)

        E = E_next

    return {
        "total_cost": total_cost,
        "buy_kwh": total_buy_kwh,
        "sell_kwh": total_sell_kwh,
        "soc": soc_history,
        "buy_flow": grid_buy_history,
        "sell_flow": grid_sell_history,
        "cost_history": cost_history
    }


res_A = simulate("A_Self_Consumption", BAT)
res_B = simulate("B_Price_Optimized", BAT)

print("\nFinal Results (Default Parameters):")
print(f"Strategy A Cost: {res_A['total_cost']:.2f} NTD (Buy: {res_A['buy_kwh']:.2f} kWh, Sell: {res_A['sell_kwh']:.2f} kWh)")
print(f"Strategy B Cost: {res_B['total_cost']:.2f} NTD (Buy: {res_B['buy_kwh']:.2f} kWh, Sell: {res_B['sell_kwh']:.2f} kWh)")
print(f"Savings (A - B): {res_A['total_cost'] - res_B['total_cost']:.2f} NTD")

hours = list(range(24))

# Plot 1: Battery SOC
plt.figure(figsize=(10, 4))
plt.plot(hours, res_A["soc"], label="Strategy A: SOC", marker="o")
plt.plot(hours, res_B["soc"], label="Strategy B: SOC", marker="x", linestyle="--")
plt.ylabel("Battery Energy (kWh)")
plt.xlabel("Hour of Day")
plt.title("Battery State of Charge (SOC) Comparison")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Plot 2: Cumulative Cost
plt.figure(figsize=(10, 4))
plt.plot(hours, res_A["cost_history"], label=f"Strategy A (Total {res_A['total_cost']:.1f} NTD)")
plt.plot(hours, res_B["cost_history"], label=f"Strategy B (Total {res_B['total_cost']:.1f} NTD)", linestyle="--")
plt.ylabel("Cumulative Cost (NTD)")
plt.xlabel("Hour of Day")
plt.title("Cumulative Cost Comparison")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Plot 3: Load vs PV
plt.figure(figsize=(10, 4))
plt.plot(hours, load, label="Load (kW)", marker="o")
plt.plot(hours, pv, label="PV (kW)", marker="x", linestyle="--")
plt.ylabel("Power (kW)")
plt.xlabel("Hour of Day")
plt.title("Load and PV Profiles (Winter Scenario)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# Plot 4: Grid Buy/Sell flow
plt.figure(figsize=(10, 4))
plt.plot(hours, res_A["buy_flow"], label="A: Grid Buy (kW)")
plt.plot(hours, res_A["sell_flow"], label="A: Grid Sell (kW)")
plt.plot(hours, res_B["buy_flow"], label="B: Grid Buy (kW)", linestyle="--")
plt.plot(hours, res_B["sell_flow"], label="B: Grid Sell (kW)", linestyle="--")
plt.ylabel("Grid Power (kW)")
plt.xlabel("Hour of Day")
plt.title("Grid Buy/Sell Power Comparison")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()



# 4. different_emax



def different_emax(emax_list):
    cost_A = []
    cost_B = []

    for emax in emax_list:
        bat2 = BAT.copy()
        bat2["E_max"] = float(emax)
        
        bat2["E_init"] = 0.5 * bat2["E_max"]

        rA = simulate("A_Self_Consumption", bat2)
        rB = simulate("B_Price_Optimized", bat2)

        cost_A.append(rA["total_cost"])
        cost_B.append(rB["total_cost"])

    return cost_A, cost_B


emax_values = [5, 8, 10, 12, 15]  
costA, costB = different_emax(emax_values)

plt.figure(figsize=(8, 4))
plt.plot(emax_values, costA, marker="o", label="Strategy A: Total Cost")
plt.plot(emax_values, costB, marker="x", linestyle="--", label="Strategy B: Total Cost")
plt.xlabel("Battery Capacity E_max (kWh)")
plt.ylabel("Total Daily Cost (NTD)")
plt.title("different_emax: Effect of Battery Capacity on Daily Cost")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("sensitivity_emax.png", dpi=300, bbox_inches="tight")
plt.show()

print("\nSensitivity Analysis Saved: sensitivity_emax.png")
