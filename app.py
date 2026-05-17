"""Cuadro de mando financiero del S&P 500 con Streamlit.

La aplicación descarga datos desde Yahoo Finance mediante yfinance,
calcula indicadores técnicos habituales y los muestra en gráficos
interactivos construidos con Plotly.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots


# -----------------------------------------------------------------------------
# Configuración general de Streamlit
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard financiero S&P 500",
    page_icon="📈",
    layout="wide",
)


TICKERS = {
    "S&P 500 (^GSPC)": "^GSPC",
    "SPDR S&P 500 ETF (SPY)": "SPY",
}
PERIODS = ["6mo", "1y", "2y", "5y", "10y", "max"]


@st.cache_data(ttl=60 * 60)
def download_market_data(ticker: str, period: str) -> pd.DataFrame:
    """Descarga datos históricos del activo seleccionado.

    Se cachea durante una hora para evitar llamadas repetidas a Yahoo Finance
    cuando el usuario cambia entre pestañas o recarga la aplicación.
    """
    data = yf.download(
        ticker,
        period=period,
        interval="1d",
        auto_adjust=False,
        progress=False,
        threads=True,
    )

    if data.empty:
        return pd.DataFrame()

    # yfinance puede devolver columnas MultiIndex en algunas versiones; se
    # simplifican para que el resto de cálculos use nombres estándar.
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)

    data = data.reset_index()
    data["Date"] = pd.to_datetime(data["Date"])
    return data


def calculate_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Calcula el RSI usando medias móviles exponenciales tipo Wilder."""
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = -delta.clip(upper=0)

    average_gain = gains.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()
    average_loss = losses.ewm(alpha=1 / window, min_periods=window, adjust=False).mean()

    relative_strength = average_gain / average_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + relative_strength))

    # Casos extremos: si no hubo pérdidas, el RSI es 100; si tampoco hubo
    # ganancias, se usa 50 como valor neutral.
    rsi = rsi.mask((average_loss == 0) & (average_gain > 0), 100)
    rsi = rsi.mask((average_loss == 0) & (average_gain == 0), 50)
    return rsi.fillna(50)


def add_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """Añade rentabilidades, medias móviles, volatilidad, RSI, MACD y drawdown."""
    df = data.copy()

    # Se prioriza Adj Close porque incorpora dividendos y ajustes corporativos;
    # si no estuviera disponible, se usa Close.
    price_column = "Adj Close" if "Adj Close" in df.columns else "Close"
    df["Price"] = pd.to_numeric(df[price_column], errors="coerce")
    df = df.dropna(subset=["Price"]).reset_index(drop=True)

    # Rentabilidad diaria y rentabilidad acumulada desde el inicio del periodo.
    df["Daily Return"] = df["Price"].pct_change()
    df["Cumulative Return"] = (1 + df["Daily Return"].fillna(0)).cumprod() - 1

    # Medias móviles simples de medio y largo plazo.
    df["SMA 50"] = df["Price"].rolling(window=50, min_periods=1).mean()
    df["SMA 200"] = df["Price"].rolling(window=200, min_periods=1).mean()

    # Volatilidad anualizada de 20 sesiones, asumiendo 252 sesiones bursátiles.
    df["Volatility 20D"] = df["Daily Return"].rolling(window=20).std() * np.sqrt(252)

    # Indicadores de momentum: RSI y MACD clásico (12, 26, 9).
    df["RSI 14"] = calculate_rsi(df["Price"], window=14)
    ema_12 = df["Price"].ewm(span=12, adjust=False).mean()
    ema_26 = df["Price"].ewm(span=26, adjust=False).mean()
    df["MACD"] = ema_12 - ema_26
    df["Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
    df["MACD Histogram"] = df["MACD"] - df["Signal"]

    # Drawdown: caída porcentual desde el máximo histórico acumulado del periodo.
    df["Running Max"] = df["Price"].cummax()
    df["Drawdown"] = df["Price"] / df["Running Max"] - 1
    df["Max Drawdown"] = df["Drawdown"].cummin()

    return df


def format_percentage(value: float) -> str:
    """Formatea porcentajes de forma segura para tarjetas KPI y ejes."""
    if pd.isna(value):
        return "N/D"
    return f"{value:.2%}"


def plot_price_and_moving_averages(df: pd.DataFrame, ticker: str) -> go.Figure:
    """Crea el gráfico de precio junto con las SMA de 50 y 200 días."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Price"], name="Precio", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA 50"], name="SMA 50", line=dict(width=1.5)))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA 200"], name="SMA 200", line=dict(width=1.5)))
    fig.update_layout(
        title=f"Precio y medias móviles - {ticker}",
        xaxis_title="Fecha",
        yaxis_title="Precio",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def plot_line(df: pd.DataFrame, column: str, title: str, yaxis_title: str) -> go.Figure:
    """Crea un gráfico de línea sencillo para series temporales."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df[column], name=column, line=dict(width=2)))
    fig.update_layout(title=title, xaxis_title="Fecha", yaxis_title=yaxis_title, hovermode="x unified")
    return fig


def plot_rsi(df: pd.DataFrame) -> go.Figure:
    """Crea el gráfico RSI con bandas de referencia de sobrecompra/sobreventa."""
    fig = plot_line(df, "RSI 14", "RSI de 14 periodos", "RSI")
    fig.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Sobrecompra")
    fig.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Sobreventa")
    fig.update_yaxes(range=[0, 100])
    return fig


def plot_macd(df: pd.DataFrame) -> go.Figure:
    """Crea un gráfico combinado con MACD, señal e histograma."""
    fig = make_subplots(specs=[[{"secondary_y": False}]])
    histogram_colors = np.where(df["MACD Histogram"] >= 0, "#2ca02c", "#d62728")

    fig.add_trace(
        go.Bar(x=df["Date"], y=df["MACD Histogram"], name="Histograma", marker_color=histogram_colors)
    )
    fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Signal"], name="Señal", line=dict(width=2)))
    fig.update_layout(
        title="MACD, línea de señal e histograma",
        xaxis_title="Fecha",
        yaxis_title="Valor",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def main() -> None:
    """Renderiza la aplicación de Streamlit."""
    st.title("📈 Cuadro de mando financiero del S&P 500")
    st.markdown(
        "Analiza el S&P 500 o el ETF SPY con indicadores de rentabilidad, "
        "tendencia, momentum, volatilidad y riesgo."
    )

    # Controles principales en la barra lateral.
    st.sidebar.header("Configuración")
    ticker_label = st.sidebar.selectbox("Activo", options=list(TICKERS.keys()))
    ticker = TICKERS[ticker_label]
    period = st.sidebar.selectbox("Periodo histórico", options=PERIODS, index=2)

    raw_data = download_market_data(ticker, period)
    if raw_data.empty:
        st.error("No se pudieron descargar datos. Intenta de nuevo o elige otro periodo.")
        st.stop()

    df = add_indicators(raw_data)
    latest = df.iloc[-1]

    st.caption(
        f"Datos de Yahoo Finance para {ticker}. Última fecha disponible: "
        f"{latest['Date'].date().isoformat()}"
    )

    # Tarjetas KPI solicitadas.
    kpi_price, kpi_return, kpi_volatility, kpi_rsi, kpi_drawdown = st.columns(5)
    kpi_price.metric("Último precio", f"{latest['Price']:,.2f}")
    kpi_return.metric("Rentabilidad total", format_percentage(latest["Cumulative Return"]))
    kpi_volatility.metric("Volatilidad actual", format_percentage(latest["Volatility 20D"]))
    kpi_rsi.metric("RSI actual", f"{latest['RSI 14']:.2f}")
    kpi_drawdown.metric("Máx. drawdown", format_percentage(df["Drawdown"].min()))

    st.divider()

    # Gráficos interactivos de Plotly.
    st.plotly_chart(plot_price_and_moving_averages(df, ticker), use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        cumulative_fig = plot_line(
            df,
            "Cumulative Return",
            "Rentabilidad acumulada",
            "Rentabilidad",
        )
        cumulative_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(cumulative_fig, use_container_width=True)

        volatility_fig = plot_line(df, "Volatility 20D", "Volatilidad anualizada a 20 días", "Volatilidad")
        volatility_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(volatility_fig, use_container_width=True)

        st.plotly_chart(plot_rsi(df), use_container_width=True)

    with col_right:
        drawdown_fig = plot_line(df, "Drawdown", "Drawdown", "Drawdown")
        drawdown_fig.update_yaxes(tickformat=".0%")
        st.plotly_chart(drawdown_fig, use_container_width=True)

        st.plotly_chart(plot_macd(df), use_container_width=True)

    with st.expander("Ver datos calculados"):
        display_columns = [
            "Date",
            "Price",
            "Daily Return",
            "Cumulative Return",
            "SMA 50",
            "SMA 200",
            "Volatility 20D",
            "RSI 14",
            "MACD",
            "Signal",
            "MACD Histogram",
            "Drawdown",
            "Max Drawdown",
        ]
        st.dataframe(df[display_columns].sort_values("Date", ascending=False), use_container_width=True)


if __name__ == "__main__":
    main()
