# Cuadro de mando financiero del S&P 500

Aplicación interactiva creada con **Python**, **Streamlit**, **yfinance**, **pandas**, **numpy** y **Plotly** para analizar el comportamiento histórico del S&P 500. Permite comparar el índice `^GSPC` con el ETF `SPY`, elegir distintos periodos de análisis y visualizar indicadores técnicos clave en tarjetas KPI y gráficos interactivos.

## Funcionalidades

- Descarga de datos históricos desde Yahoo Finance con `yfinance`.
- Selector de activo: `^GSPC` o `SPY`.
- Selector de periodo: `6mo`, `1y`, `2y`, `5y`, `10y` o `max`.
- Cálculo de rentabilidad diaria, rentabilidad acumulada, medias móviles, volatilidad, RSI, MACD y drawdown.
- Tarjetas KPI con último precio, rentabilidad total, volatilidad actual, RSI actual y máximo drawdown.
- Gráficos interactivos con Plotly para precio, rentabilidad acumulada, drawdown, volatilidad, RSI y MACD.

## Instalación

Ejecuta estos comandos desde la raíz del proyecto usando Anaconda:

```bash
conda create -n dashboard-sp500 python=3.11
conda activate dashboard-sp500
pip install -r requirements.txt
```

## Ejecución

Con el entorno `dashboard-sp500` activado, inicia la aplicación con:

```bash
streamlit run app.py
```

Streamlit abrirá el cuadro de mando en el navegador. Si no se abre automáticamente, copia la URL local que aparece en la terminal.

## Indicadores incluidos

- **Rentabilidad diaria**: variación porcentual del precio ajustado entre una sesión y la sesión anterior.
- **Rentabilidad acumulada**: rendimiento total acumulado desde el primer día del periodo seleccionado.
- **SMA 50**: media móvil simple de 50 sesiones; ayuda a observar tendencias de corto y medio plazo.
- **SMA 200**: media móvil simple de 200 sesiones; suele usarse como referencia de tendencia de largo plazo.
- **Volatilidad anualizada a 20 días**: desviación estándar de las rentabilidades diarias de las últimas 20 sesiones, anualizada con 252 sesiones bursátiles.
- **RSI de 14 periodos**: oscilador de momentum entre 0 y 100. Valores por encima de 70 suelen asociarse con sobrecompra y valores por debajo de 30 con sobreventa.
- **MACD**: diferencia entre las medias exponenciales de 12 y 26 sesiones; se compara con una línea de señal de 9 sesiones.
- **Histograma MACD**: diferencia entre el MACD y la línea de señal; muestra cambios en el momentum.
- **Drawdown**: caída porcentual del precio desde el máximo acumulado del periodo.
- **Máximo drawdown**: peor caída porcentual observada dentro del periodo seleccionado.

## Estructura del proyecto

```text
.
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Nota

Los datos proceden de Yahoo Finance y pueden tener retrasos, ajustes o cambios de disponibilidad. Esta aplicación es educativa y no constituye asesoramiento financiero.
