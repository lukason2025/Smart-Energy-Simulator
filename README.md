# Smart Energy Management Simulator
---
## 1. Project Overview
This project is a Python-based simulator for household energy management with a **Rooftop PV system** and a **Battery Energy Storage System (BESS)**.

The simulator runs a **24-hour (hourly step) Taiwan winter scenario (December)** and compares two operating strategies to show how control logic changes:
* Grid purchase/sales behavior
* Battery State-of-Charge (SOC)
* Total daily electricity cost

This is a simplified **smart-grid / microgrid style** household scenario, where distributed resources (PV + battery) respond to price signals (TOU, FIT) to change grid interaction.

### Key Objectives
1. **Quantify Energy Flows:** Track the balance between Load, PV generation, Battery charge/discharge, and Grid exchange.
2. **Compare Strategies:** Evaluate cost differences between **Self-Consumption** and **Price-Based** control.
3. **Apply Engineering Concepts:** Model the battery using a discrete-time balance equation (**Accumulation = Input − Output ± Losses**).

---

## 2. Operating Strategies

### Strategy A: Self-Consumption Priority (Eco-Mode)
* **Goal:** Maximize the usage of locally generated solar power.
* **Logic:**
  * PV generation is used to cover the load first.
  * Surplus PV is charged into the battery (within limits).
  * The battery discharges when there is a deficit (**Load > PV**).
  * Grid import is used only when the battery cannot cover the remaining deficit.
  * Grid export occurs only when PV surplus remains after charging.

### Strategy B: Price-Based Optimization (Economic Mode)
* **Goal:** Minimize daily electricity cost by exploiting **Time-of-Use (TOU)** prices.
* **Logic (heuristic rule-based control):**
  * **Charge** during **Off-Peak (離峰)** hours (cheap price).
  * **Discharge** during **Semi-Peak (半尖峰)** hours (higher price) to reduce expensive grid purchases.
  * *Note:* In the **non-summer season (Oct–May)** for the selected TOU case, there is no **Peak (尖峰)** rate; only **Off-Peak (離峰)** and **Semi-Peak (半尖峰)** apply.
  * Battery export is not used in this project (battery discharges to cover deficits, not to sell). PV surplus can still be exported if the battery is full.

---

## 3. Data Assumptions & References (Taiwan Winter Scenario)
This simulation uses an assumed household scenario with official tariff references (TOU, FIT) and climate statistics support.

### 3.1. Data Sources (Assumptions)
* **Load Profile:** A simplified Taiwanese residential pattern with an evening peak (18:00–22:00).
* **PV Generation Profile:** A simplified 5 kWp rooftop PV curve for Taipei in winter, constructed to be consistent with shorter daylight conditions in December and supported by CWA monthly climate statistics (Sunshine Duration, 日照時數).
* **Electricity Pricing (Official Regulations):**
  * **Buying Price:** Taipower **表燈簡易型時間電價 (3段式) – 非夏月** (effective **2025-10-01**).
    * Off-Peak (離峰): **1.99 NTD/kWh**
    * Semi-Peak (半尖峰): **4.48 NTD/kWh**
  * **Selling Price:** MOEA **2025 Feed-in Tariff (FIT)** for rooftop PV < 10 kW.
    * December scenario uses **Phase 2**.
    * Rate: **5.6279 NTD/kWh** (MOEA announcement dated **2025-03-07**).

### 3.2. References (Official Links)
1. **Taipower Official Rate Table (Effective 2025-10-01):**
   * https://www.taipower.com.tw/media/ba2angqi/%E5%90%84%E9%A1%9E%E9%9B%BB%E5%83%B9%E8%A1%A8%E5%8F%8A%E8%A8%88%E7%AE%97%E7%AF%84%E4%BE%8B.pdf?mediaDL=true  
   * Refer to: 表燈簡易型時間電價 (3段式) – 非夏月  
   * Accessed: 2025-12-25
2. **MOEA 2025 Renewable Energy FIT Rates (Announcement 2025-03-07):**
   * https://www.moea.gov.tw/Mns/english/news/News.aspx?kind=6&menu_id=176&news_id=118710  
   * Accessed: 2025-12-25
3. **CWA Monthly Climate Statistics (Monthly Data):**
   * https://www.cwa.gov.tw/V8/C/C/Statistics/monthlydata.html  
   * Refer to: Sunshine Duration (日照時數)  
   * Accessed: 2025-12-25

### 3.3. Additional Engineering References (Parameter Basis)
To ensure the realism of the simulation, the following engineering parameters were derived from official/industry references.

**1. Battery Power Rating Basis (3.3 kW):**
* **Source:** Tesla Powerwall 2 AC Datasheet (Feb 2020, UK)
* **Link:** https://www.tesla.com/sites/default/files/pdfs/powerwall/Powerwall2ACDatasheet_EN_UK_feb2020.pdf
* **Evidence in Datasheet:** The datasheet footnote states the provided performance values are at **3.3 kW charge/discharge power**.
* **Engineering Logic:** In this project, `P_ch_max = 3.3` and `P_dis_max = 3.3` are used as a conservative residential BESS charge/discharge rating consistent with the datasheet’s stated test condition.
* Accessed: 2025-12-25

**2. Residential Load Profile (Winter Evening Peak):**
* **Source:** U.S. Energy Information Administration (EIA) - “Hourly electricity consumption varies throughout the day and across seasons”
* **Link:** https://www.eia.gov/todayinenergy/detail.php?id=42915
* **Engineering Logic:** The report supports the common residential pattern where demand peaks in the evening during winter (lighting/heating-related usage). This supports using an evening peak in the constructed load profile.
* Accessed: 2025-12-25

**3. Battery Efficiency (eta = 0.95) from Round-Trip Efficiency:**
* **Source:** Tesla Powerwall 2 AC Datasheet (Feb 2020, UK)
* **Link:** https://www.tesla.com/sites/default/files/pdfs/powerwall/Powerwall2ACDatasheet_EN_UK_feb2020.pdf
* **Evidence in Datasheet:** Round Trip Efficiency is listed as **90%** (AC-to-battery-to-AC).
* **Engineering Logic:** The simulation uses separate charge/discharge efficiencies, so the one-way efficiency is approximated as `eta = sqrt(0.90) ≈ 0.95`.
* Accessed: 2025-12-25

---

## 4. Mathematical Model (Chemical Engineering Context)
The battery is treated as a dynamic unit operation governed by a discrete-time balance equation.

### 4.1. Balance Concept
> **Accumulation = Input − Output (± Losses)**

### 4.2. Difference Equation (dt = 1 h)
```text
E_next = E_current + (eta_ch * P_ch - P_dis / eta_dis) * dt

Where:
  E_current, E_next : Battery energy state (kWh)
  P_ch, P_dis       : Charging / Discharging power (kW)
  eta_ch, eta_dis   : Efficiency factors (–)
  dt                : Time step (h), dt = 1.0

Constraints:
  0 <= E <= E_max
  0 <= P_ch <= P_ch_max
  0 <= P_dis <= P_dis_max
```

### 4.3. Cost Accounting (per hour)
```text
If P_grid > 0:  cost += P_grid * price_buy[t]  * dt   (Buying cost)
If P_grid < 0:  cost += P_grid * price_sell[t] * dt   (Selling revenue; negative cost)
```

---

## 5. Adjustable Variables (Affecting the Outcome)
The final daily cost, SOC profile, and grid dependency can change depending on these variables.

### 5.1. PV and Load
* `load[24]` (kW): Household demand profile  
* `pv[24]` (kW): PV generation profile (season, weather, PV size)  
* **PV scaling:** Changing PV capacity scales the `pv[24]` curve  

### 5.2. Tariff / Market Parameters
* `price_buy[24]` (NTD/kWh): TOU buying price schedule  
* `price_sell[24]` (NTD/kWh): FIT/PPA-like selling price (fixed in this simplified model)  

### 5.3. Battery Parameters
* `E_max` (kWh): Battery energy capacity  
* `E_init` (kWh): Initial battery energy (initial SOC)  
* `P_ch_max`, `P_dis_max` (kW): Max charge/discharge power  
* `eta_ch`, `eta_dis` (–): Efficiencies  

### 5.4. Strategy Parameters (Heuristic Thresholds)
* `curr_price < 2.5` → Charge  
* `curr_price > 4.0` → Discharge  

---

## 6. Outputs

### Terminal output
* Total daily cost (NTD)
* Total grid purchase (kWh)
* Total grid sales (kWh)
* Savings (A − B)

### Plots
1. Battery SOC comparison
2. Cumulative cost comparison
3. Load vs PV profiles
4. Grid buy/sell power flow comparison
5. Sensitivity analysis plot (Battery capacity vs Total daily cost)

---

## 7. Sensitivity Analysis (Adjustable Variable Demonstration)
This project varies Battery Capacity (**E_max**) while keeping the initial SOC at 50%:

```text
E_init = 0.5 * E_max
```

**Sweep:**
* `E_max = [5, 8, 10, 12, 15]` kWh

**Result:**
* Plots total daily cost of Strategy A vs Strategy B
* Saves the figure as `sensitivity_emax.png`

---

## 8. How to Run

### Prerequisites
* Python 3.x
* `matplotlib`

### Execution
1. Clone this repository or download `main.py`
2. Run:
```bash
python main.py
```
3. Check:
* Terminal results
* Generated plots (including `sensitivity_emax.png`)

---

## 9. Program Architecture (Code Structure)

This section outlines how the Python script is structured to process data and simulate energy flows.

### 9.1. Data Setup
* **Time Resolution:** The simulation uses a time step of `DT = 1.0` hour over a 24-hour horizon.
* **Profiles:** Defines 24-hour arrays for `load`, `pv`, `price_buy`, and `price_sell`.
* **Parameters:** Stores battery specs in a dictionary `BAT` (including `E_max`, `E_init`, `P_ch_max`, `P_dis_max`, `eta_ch`, `eta_dis`).

### 9.2. Core Simulator Function
The `simulate(strategy_name, bat_params)` function handles the hour-by-hour logic (`t = 0 ... 23`):
1. **Net Load Calculation:** Computes `net_load = load[t] - pv[t]` to determine immediate deficit or surplus.
2. **Decision Making:** Determines charging (`P_ch`) and discharging (`P_dis`) power based on the selected **Strategy Logic**.
3. **State Update:** Updates battery energy using the difference equation and clamps it within bounds (`0 <= E <= E_max`).
4. **Cost Accumulation:** Records hourly costs/revenues and saves history lists (`soc`, `buy_flow`, `sell_flow`, `cost_history`).

### 9.3. Strategy Layer (Inside Simulation)
* **Strategy A (Self-Consumption):**
  * Prioritizes covering load with PV.
  * Surplus charges battery first; remaining surplus is sold.
  * Deficit is met by battery discharge first; remaining deficit is bought from grid.
* **Strategy B (Price-Based):**
  * Uses TOU price thresholds.
  * **Cheap:** Force charge.
  * **Expensive:** Force discharge (to cover load only; no battery export).
  * **Normal:** Default to self-consumption logic.

### 9.4. Visualization & Analysis
* **Plotting:** Generates **5 plots** using `matplotlib`:
  * 4 comparison plots (SOC, Cost, Load vs PV, Grid buy/sell flow)
  * 1 sensitivity analysis plot (Battery capacity vs Total daily cost)
* **Sensitivity Analysis Module:** The sensitivity function iteratively runs the simulator with varying `E_max` values (while scaling `E_init`) to quantify the economic impact of battery size.

### 9.5. File Structure
* `main.py` : Complete simulation source code
* `README.md` : Project documentation
* `sensitivity_emax.png` : Generated result image

---

## 10. Development Process

This project was developed through the following systematic 5-step process, ranging from designing a scenario reflecting Taiwan's actual power environment to implementing algorithms and conducting sensitivity analysis.

### 10.1. Scenario Data Construction & Engineering Basis
First, to set parameters for each smart grid strategy, I defined a specific scenario of **'December (Winter) in Taiwan'** and constructed the necessary data based on engineering grounds using Python lists.
* **Data Construction:** Considering the winter context, the `pv` list assumes a 5.0 kWp panel but limits the maximum output to **3.5 kW**. This **70% derating assumption** was applied to reflect the low solar angle and cloudy weather in Taipei, referencing **CWA sunshine duration statistics**, with generation hours limited to 07:00–17:00.
* **Parameter Setup:** Battery specifications were defined in the `BAT` dictionary. For a fair test, `E_init` was set to **50% of capacity**, charge/discharge rates (`P_ch_max`/`P_dis_max`) to **3.3**, and efficiency `eta` to **0.95**. Electricity prices (`price_buy`, `price_sell`) were adopted from official Taipower and MOEA documents.

### 10.2. Comparative Strategy Design (Strategy A vs B)
To compare performance, I designed two contrasting logic flows within the `simulate(strategy_name, bat_params)` function.
* **Simulation A (Self-Consumption):** Prioritizes physical energy self-sufficiency without economic variables. It follows a basic logic of charging surplus energy and discharging for deficits.
* **Simulation B (Price Optimization):** Utilizes the TOU rate structure to minimize costs. It is designed to force-charge when `price_buy` is low and force-discharge when prices are high to reduce expensive grid purchases.

### 10.3. Core Implementation (Main Simulation Logic)
The core simulation engine was implemented within a loop iterating through 24 hours (`for t in range(24):`) with a time step of `DT=1.0`.
1. **Net Load Calculation:** In each step, `net_load = P_load - P_pv` was calculated to determine the power balance (Positive: Deficit, Negative: Surplus).
2. **Decision Making:**
   * **Strategy A:** When `net_load < 0`, the battery charges within limits using `P_ch = min(surplus, P_ch_max, (E_max-E)/eta)`. When `net_load > 0`, it discharges using `P_dis = min(deficit, ...)`.
   * **Strategy B:** It uses conditional logic based on price. `if curr_price < 2.5:` detects cheap periods for max-speed charging (`P_ch = min(...)`). `elif curr_price > 4.0 and net_load > 0:` triggers discharging only when there is an actual deficit (this prevents a surplus-time bug where energy could “disappear” by forcing discharge when `net_load <= 0`). To enforce **"No Battery Export,"** discharge is constrained to cover only household shortage: `P_dis = min(deficit, ...)`.
3. **Battery State Update (Difference Equation):** I applied a chemical engineering mass balance concept to form the difference equation:
   * `E_next = E + (eta_ch * P_ch - P_dis / eta_dis) * DT`
   * I multiplied efficiency (`* eta`) during charging and divided by efficiency (`/ eta`) during discharging to reflect losses, using `max(0.0, min(E_max, E_next))` to clamp SOC within **0–E_max**.
4. **Cost Calculation:** I wrote logic to accumulate `total_cost` by adding costs (`+= P_grid * price_buy`) if `P_grid > 0` (Import) and subtracting revenue (adding negative cost) if `P_grid < 0` (Export).

### 10.4. Visualization
To verify the integrity of the implemented logic, I used `matplotlib` to generate **5 plots** (4 comparison plots + 1 sensitivity plot). Using list data collected during simulation (e.g., `soc_history`, `cost_history`, `grid_buy_flow`), I visually confirmed the physical validity of battery behavior and the peak-shaving effect of Strategy B (comparing solid vs. dashed lines).

### 10.5. Sensitivity Analysis
Finally, to analyze how economics change with the system's largest variable, **'Total Battery Capacity,'** I implemented a separate function `sensitivity_sweep_emax(emax_list)`.
* **Parameter Control:** I prevented global variable contamination by using `BAT.copy()` inside the `for emax in emax_list:` loop.
* **Fair Comparison Logic:** To solve the issue where simply increasing capacity changes the initial SOC ratio, I added code to auto-correct the initial state: `current_bat["E_init"] = 0.5 * current_bat["E_max"]`, ensuring all cases start at 50% SOC.
* The results were collected in `cost_A` and `cost_B` lists to derive a plot showing cost reduction trends vs. capacity, completing the development.

---

## 11. Modifications & Change Log

This project underwent the following modifications and enhancements during the development process to resolve issues and increase the realism of the simulation.

### 11.1. Methodology Shift (Optimization -> Simulation)
Initially, I approached this as a mathematical optimization problem (like Linear Programming) to minimize total costs. However, defining decision variables for every hour and formulating complex constraints made the implementation difficult and reduced code transparency. Therefore, I shifted the design to a **Scenario-based Simulation** method. I collected actual Taiwan TOU rates and solar data to build the environment and directly implemented the battery difference equation and cost accumulation logic to improve code clarity and explainability.

### 11.2. Logic Refinement: Discharge Limit (Deficit-Only, No Battery Export)
While testing Strategy B (Price Optimization), I discovered a critical inefficiency. The initial logic could discharge too aggressively during **high-price (semi-peak) periods**, depleting the battery early or causing unnecessary export. To solve this, I added a constraint: **"Discharge covers only the household power deficit"** (`P_dis = min(deficit, ...)`). This modification aligns the model with realistic residential BESS operation (backup and cost-saving) rather than merchant export.

### 11.3. Bug Fix (Prevent Surplus-Time Forced Discharge)
A specific bug was identified in Strategy B: if the code forced discharge whenever `curr_price > 4.0`, it could trigger even when `net_load <= 0` (PV surplus). This could create an “energy disappearing” behavior in the accounting. I fixed this by adding an explicit condition:
* `elif curr_price > 4.0 and net_load > 0:`
This ensures forced discharge happens only when there is a real household deficit.

### 11.4. Scenario Selection (Winter Scenario)
Choosing the seasonal scenario required engineering judgment. Summer and Winter have vastly different peak load times and solar generation hours. I selected **December (Winter)** as it is most relevant to the current season. Since winter has shorter daylight hours and less generation, energy is scarce, making efficient management crucial. This characteristic of the winter scenario resulted in clearer performance differences between Strategy A and Strategy B compared to a summer scenario.

### 11.5. Sensitivity Analysis for Variable Expansion
Beyond single-condition simulation, I wanted to understand how the system's key hardware variable, **'Battery Capacity (E_max),'** affects the results. To achieve this, I added a `for` loop at the end of the main logic to iterate through capacities of `[5, 8, 10, 12, 15]` kWh. I built an automated test bench that not only changes the capacity but also automatically adjusts the initial SOC ratio (maintaining 50%), allowing for a quantitative analysis of economic trends based on battery size.

### 11.6. Physical Modeling Corrections (Efficiency + Unit Consistency)
In the initial implementation, I used an ideal model without considering conversion losses, but confirmed that this led to discrepancies from real battery behavior. Based on Tesla Powerwall 2 datasheet (Round Trip Efficiency 90%), I applied `eta = 0.95` (one-way, approximated by `sqrt(0.90)`). I modified the equations to multiply efficiency during charging and divide by efficiency during discharging. Additionally, I applied `DT=1.0` consistently so that Power (kW) × Time (h) = Energy (kWh) is preserved in all updates.

---

## 12. Limitations

Although this project successfully demonstrates the economic logic of BESS operations based on Taiwan's specific tariff system, several simplifications were made that limit its direct application to real-world engineering.

First, the simulation operates on a **1-hour time step (dt = 1.0 h)**. While sufficient for economic analysis, this coarse temporal resolution fails to capture sub-hourly power fluctuations (transient dynamics) or minute-level peak loads that occur in actual household usage.

Second, the battery model focuses on energy balance but **neglects electrochemical degradation**. In reality, frequent charging and discharging accelerate battery aging (capacity loss). By ignoring cycle life costs and degradation penalties, the current model may slightly overestimate the long-term economic benefits.

Third, **grid and policy constraints were simplified**. The model assumes the grid can accept infinite power export/import without physical limitations (e.g., transformer capacity, voltage rise issues). Also, complex real-world FIT eligibility rules or export caps were simplified to a fixed selling price.

Lastly, **Strategy B relies on heuristic rules** (threshold-based control) rather than mathematical optimization. While this approach offers high transparency and explainability, it does not guarantee a mathematically global optimum compared to advanced solvers like Mixed-Integer Linear Programming (MILP) or Dynamic Programming.



