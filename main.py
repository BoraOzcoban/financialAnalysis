from yahooquery import Ticker
import yfinance as yfin
yfin.pdr_override()

# Data Extraction
ticker = "C"
t = Ticker(ticker)
df = t.income_statement(frequency='q')
dt = t.cash_flow(frequency="q")
db = t.balance_sheet(frequency="q")
ds = t.valuation_measures
da = t.key_stats
dl = t.financial_data

shares = da.get(ticker, {}).get("sharesOutstanding")
sharesF = da.get(ticker, {}).get("floatShares")
tax = df[['asOfDate', 'TaxProvision']]
ebitda = df[['asOfDate', 'EBITDA']]
capex = dt[['asOfDate', 'CapitalExpenditure']]
change_nwc = dt[['asOfDate', 'ChangeInWorkingCapital']]
ev = ds[['asOfDate', 'EnterpriseValue']]
cash = db[['asOfDate', 'CashAndCashEquivalents']]
debt = db[['asOfDate', 'TotalDebt']]
evEbitda = ds[['asOfDate', 'EnterprisesValueEBITDARatio']]
marketCap = ds[['asOfDate', 'MarketCap']]
cashFlow = dt[['asOfDate', 'FreeCashFlow']]
evSales = ds[['asOfDate', 'EnterprisesValueRevenueRatio']]
evEbitda = ds[['asOfDate', 'EnterprisesValueEBITDARatio']]
pe = ds[['asOfDate', 'PeRatio']]
debt = db[['asOfDate', 'TotalDebt']]
equity = db[['asOfDate', 'TotalEquityGrossMinorityInterest']]
totcap = db[['asOfDate', 'TotalCapitalization']]
taxRate = df[['asOfDate', 'TaxRateForCalcs']]
roe = dl.get(ticker, {}).get("returnOnEquity")


########################################################################################################################
indexNumber = -1
while indexNumber >= -5:
    # Discounted Cash Flow Calculation
    unleveredFcf = ebitda["EBITDA"][indexNumber] - tax["TaxProvision"][indexNumber] - capex["CapitalExpenditure"][indexNumber] - \
                   change_nwc["ChangeInWorkingCapital"][indexNumber]
    transactionCf = unleveredFcf * 1

    # Intrinsic Value Calculation
    intrinsicValue = ev['EnterpriseValue'][indexNumber] + cash['CashAndCashEquivalents'][indexNumber] - debt['TotalDebt'][indexNumber]

    # Market Value Calculation
    enterpriseValue = marketCap["MarketCap"][indexNumber] + debt["TotalDebt"][indexNumber] - cash["CashAndCashEquivalents"][indexNumber]

    # WACC Calculations
    debtToCap = debt["TotalDebt"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
    equityToCap = equity["TotalEquityGrossMinorityInterest"][indexNumber] / totcap["TotalCapitalization"][indexNumber]
    debtToEquity = debtToCap = debt["TotalDebt"][indexNumber] / equity["TotalEquityGrossMinorityInterest"][indexNumber]

    # Output
    print("------------------------")
    print(f"Intrinsic Value EV/Share: {intrinsicValue / shares}")
    print(f"Market Value EV/Share: {enterpriseValue / sharesF}")
    print(f"Upside: {intrinsicValue / shares - enterpriseValue / sharesF}")
    print(f"EV/Sales: {evSales['EnterprisesValueRevenueRatio'][indexNumber]}")
    print(f"EV/EBITDA: {evEbitda['EnterprisesValueEBITDARatio'][indexNumber]}")
    print(f"P/E: {pe['PeRatio'][indexNumber]}")
    indexNumber = indexNumber - 1

# Discount Rate Calculation
n = 0
while n < cashFlow["FreeCashFlow"].size - 1:
    totalCF = cashFlow["FreeCashFlow"][n]
    n = n + 1
discountRate = (totalCF / transactionCf) - 1

# Terminal Value Calculation
o = 0
perpetualGrowth = 0
while o < cashFlow["FreeCashFlow"].size - 1:
    perpetualGrowth = perpetualGrowth + (cashFlow["FreeCashFlow"][o] / ((1 + discountRate) ** (o + 1)))
    o = o + 1
terminalValue = (perpetualGrowth + evEbitda["EnterprisesValueEBITDARatio"][-1]) / 2
print(f"Terminal Value: {terminalValue}")

