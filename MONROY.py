import itertools
import streamlit as st

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
  for exp in range(0, 7):
    for val in base:
      values.append(val * (10**exp))
  return values


def calc_parallel(r1, r2):
  return (r1 * r2) / (r1 + r2) if (r1 + r2) > 0 else 0


def format_resistance(val):
  if val >= 1e6:
    return f"{val / 1e6:.3f} MΩ".rstrip("0").rstrip(".")
  elif val >= 1e3:
    return f"{val / 1e3:.3f} kΩ".rstrip("0").rstrip(".")
  else:
    return f"{val:.2f} Ω".rstrip("0").rstrip(".")


def find_best_combinations(target, tolerance, max_results=8):
  resistors = get_commercial_values(tolerance)
  results = []

  # 1. Una resistencia
  for r1 in resistors:
    error = abs(r1 - target) / target * 100
    results.append((error, r1, f"{format_resistance(r1)} (Solo)"))

  # 2. Dos resistencias
  for r1, r2 in itertools.combinations_with_replacement(resistors, 2):
    eq = r1 + r2
    error = abs(eq - target) / target * 100
    results.append(
        (
            error,
            eq,
            f"{format_resistance(r1)} + {format_resistance(r2)} (Serie)",
        )
    )

    eq = calc_parallel(r1, r2)
    if eq > 0:
      error = abs(eq - target) / target * 100
      results.append(
          (
              error,
              eq,
              f"{format_resistance(r1)} || {format_resistance(r2)} (Paralelo)",
          )
      )

  # 3. Tres resistencias
  for r1, r2, r3 in itertools.combinations_with_replacement(resistors, 3):
    eq = r1 + r2 + r3
    error = abs(eq - target) / target * 100
    results.append(
        (
            error,
            eq,
            f"({format_resistance(r1)} + {format_resistance(r2)} + {format_resistance(r3)}) (Serie)",
        )
    )

    p1 = calc_parallel(r1, r2)
    eq = calc_parallel(p1, r3)
    if eq > 0:
      error = abs(eq - target) / target * 100
      results.append(
          (
              error,
              eq,
              f"({format_resistance(r1)} || {format_resistance(r2)} || {format_resistance(r3)}) (Paralelo)",
          )
      )

    eq = calc_parallel(r1 + r2, r3)
    if eq > 0:
      error = abs(eq - target) / target * 100
      results.append(
          (
              error,
              eq,
              f"({format_resistance(r1)} + {format_resistance(r2)}) || {format_resistance(r3)} (Mixta)",
          )
      )

    eq = calc_parallel(r1, r2) + r3
    error = abs(eq - target) / target * 100
    results.append(
        (
            error,
            eq,
            f"({format_resistance(r1)} || {format_resistance(r2)}) + {format_resistance(r3)} (Mixta)",
        )
    )

  results.sort(key=lambda x: x[0])

  unique_results = []
  seen = set()
  for item in results:
    val_rounded = round(item[1], 3)
    if val_rounded not in seen:
      seen.add(val_rounded)
      unique_results.append(item)
    if len(unique_results) >= max_results:
      break

  return unique_results


# Configuración de la página web
st.set_page_config(
    page_title="Optimizador de Resistencias", page_icon="⚡", layout="centered"
)

st.title("⚡ Optimizador de Redes de Resistencias")
st.markdown(
    "Calcula automáticamente las mejores combinaciones de resistencias"
    " comerciales (E12 / E24) en **serie, paralelo o redes mixtas** para"
    " alcanzar un valor objetivo con el menor error posible."
)

st.divider()

# Panel de entradas
col1, col2 = st.columns(2)
with col1:
  target_str = st.text_input("Valor Objetivo (Ohms):", value="330")
with col2:
  tolerance = st.radio(
      "Tolerancia:",
      [10, 1],
      format_func=lambda x: "10% (E12)" if x == 10 else "1% (E24)",
  )

if st.button("Calcular Combinaciones", type="primary", use_container_width=True):
  try:
    target = float(target_str)
    if target <= 0:
      raise ValueError
  except ValueError:
    st.error("Por favor ingresa un valor de resistencia válido mayor a 0.")
    st.stop()

  with st.spinner("Buscando las mejores combinaciones..."):
    best_results = find_best_combinations(target, tolerance, max_results=8)

  st.success("¡Cálculo finalizado con éxito!")

  # Formatear datos para la tabla web
  table_data = []
  for i, (error, equiv, config) in enumerate(best_results, 1):
    table_data.append({
        "#": i,
        "Topología y Componentes": config,
        "Valor Equivalente": format_resistance(equiv),
        "Error (%)": f"{error:.2f}%",
    })

  st.markdown("### Mejores Combinaciones Encontradas")
  st.table(table_data)