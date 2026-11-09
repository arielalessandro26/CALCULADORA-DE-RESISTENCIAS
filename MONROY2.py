import itertools
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Calculadora de Resistencias", page_icon="⚡", layout="centered"
)

st.title("⚡ Optimizador de Redes de Resistencias")
st.markdown(
    "Calcula la mejor combinación comercial de 1, 2 o 3 resistencias (Serie,"
    " Paralelo y Mixtas)."
)

# Series comerciales estándar
E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E24 = [
    1.0,
    1.1,
    1.2,
    1.3,
    1.5,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.7,
    3.0,
    3.3,
    3.6,
    3.9,
    4.3,
    4.7,
    5.1,
    5.6,
    6.2,
    6.8,
    7.5,
    8.2,
    9.1,
]


def get_commercial_values(tolerance):
  base = E12 if tolerance == 10 else E24
  values = []
  for exp in range(0, 7):  # De 1 Ohm a 1 Megaohm
    for val in base:
      values.append(val * (10**exp))
  return values


def calc_parallel(r1, r2):
  return (r1 * r2) / (r1 + r2) if (r1 + r2) > 0 else 0


def format_resistor(val):
  """Formatea los valores en Ohms, kOhms o MOhms para legibilidad."""
  if val >= 1e6:
    return f"{val/1e6:g} MΩ"
  elif val >= 1e3:
    return f"{val/1e3:g} kΩ"
  else:
    return f"{val:g} Ω"


def find_best_combinations(target, tolerance, max_results=8):
  resistors = get_commercial_values(tolerance)
  results = []

  # 1. Una resistencia
  for r1 in resistors:
    error = abs(r1 - target) / target * 100
    results.append((error, r1, f"{format_resistor(r1)} (Solo)"))

  # 2. Dos resistencias
  for r1, r2 in itertools.combinations_with_replacement(resistors, 2):
    # Serie
    eq = r1 + r2
    error = abs(eq - target) / target * 100
    results.append(
        (error, eq, f"{format_resistor(r1)} + {format_resistor(r2)} (Serie)")
    )

    # Paralelo
    eq = calc_parallel(r1, r2)
    if eq > 0:
      results.append(
          (
              abs(eq - target) / target * 100,
              eq,
              f"{format_resistor(r1)} || {format_resistor(r2)} (Paralelo)",
          )
      )

  # 3. Tres resistencias (Evaluación estricta de topologías)
  for r1, r2, r3 in itertools.combinations_with_replacement(resistors, 3):
    # 3.1 Serie pura: R1 + R2 + R3
    eq = r1 + r2 + r3
    results.append((
        abs(eq - target) / target * 100,
        eq,
        f"({format_resistor(r1)} + {format_resistor(r2)} +"
        f" {format_resistor(r3)}) (Serie)",
    ))

    # 3.2 Paralelo puro: R1 || R2 || R3
    p1 = calc_parallel(r1, r2)
    eq = calc_parallel(p1, r3)
    if eq > 0:
      results.append((
          abs(eq - target) / target * 100,
          eq,
          f"({format_resistor(r1)} || {format_resistor(r2)} ||"
          f" {format_resistor(r3)}) (Paralelo)",
      ))

    # 3.3 Mixtas: (R1 + R2) || R3 y permutaciones
    for a, b, c in [(r1, r2, r3), (r1, r3, r2), (r2, r3, r1)]:
      eq = calc_parallel(a + b, c)
      if eq > 0:
        results.append((
            abs(eq - target) / target * 100,
            eq,
            f"({format_resistor(a)} + {format_resistor(b)}) ||"
            f" {format_resistor(c)} (Mixta)",
        ))

    # 3.4 Mixtas: (R1 || R2) + R3 y permutaciones
    for a, b, c in [(r1, r2, r3), (r1, r3, r2), (r2, r3, r1)]:
      eq = calc_parallel(a, b) + c
      if eq > 0:
        results.append((
            abs(eq - target) / target * 100,
            eq,
            f"({format_resistor(a)} || {format_resistor(b)}) +"
            f" {format_resistor(c)} (Mixta)",
        ))

  # Ordenar por menor error porcentual
  results.sort(key=lambda x: x[0])

  # Filtrar duplicados cercanos
  unique_results = []
  seen = set()
  for item in results:
    val_rounded = round(item[1], 2)
    if val_rounded not in seen:
      seen.add(val_rounded)
      unique_results.append(item)
    if len(unique_results) >= max_results:
      break

  return unique_results


# Controles en la interfaz web
col1, col2 = st.columns(2)

with col1:
  target_val = st.number_input(
      "Valor Objetivo de Resistencia (Ω):",
      min_value=0.1,
      value=45817.0,
      step=1.0,
  )

with col2:
  tolerance_val = st.selectbox(
      "Tolerancia deseada:", options=[1, 10], format_func=lambda x: f"{x}%"
  )

if st.button("Calcular Combinaciones", type="primary"):
  best_results = find_best_combinations(target_val, tolerance_val)

  st.subheader("📋 Mejores Resultados Encontrados")

  table_data = []
  for i, (error, equiv, config) in enumerate(best_results, 1):
    table_data.append({
        "Ranking": f"#{i}",
        "Topología y Componentes": config,
        "Valor Equivalente": format_resistor(equiv),
        "Error (%)": f"{error:.3f}%",
    })

  st.table(table_data)