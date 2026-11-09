
import os
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from home import build_home
from theme import (
    NAVY, NAVY_2, BLUE, BLUE_2, CYAN, GREEN, RED, AMBER,
    TEXT, MUTED, GRID, INSTITUTIONAL_PALETTE, TYPE_COLORS,
    STATUS_COLORS, TIME_COLORS, HEATMAP_SCALE
)

# ============================================================
# DASHBOARD GERENCIAL | PROYECTO AVISOS | EQUIPO 2
# Base: registros con marca = normal (2.815 avisos)
# Fecha de corte de los avisos abiertos: 06-may-2023
# ============================================================

app = Dash(__name__, title="Gestión Gerencial de Avisos | Equipo 2",
           suppress_callback_exceptions=True)
server = app.server

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "data", "avisos.csv"), low_memory=False)

# Tipificación y limpieza
for c in ["Fecha de aviso", "Fecha de cierre"]:
    df[c] = pd.to_datetime(df[c], errors="coerce")
for c in ["Días abierto", "Prioridad días", "Cumple prioridad días",
          "Cumple prioridad periodos", "Año", "nMes", "Año cierre",
          "Latitud", "Longitud"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
for c in ["Tipo de aviso", "Sector", "Prioridad", "Estado aviso",
          "Tiempo aviso", "Departamento", "Municipio", "CTE", "Mes"]:
    df[c] = df[c].fillna("Sin dato").astype(str).str.strip()

# El alcance del plan de trabajo es marca = normal.
df = df[df["marca"].astype(str).str.lower().eq("normal")].copy()
df["Mes fecha"] = df["Fecha de aviso"].dt.to_period("M").dt.to_timestamp()
df["Mes cierre fecha"] = df["Fecha de cierre"].dt.to_period("M").dt.to_timestamp()
df["Cumplimiento cerrado"] = np.where(
    df["Estado aviso"].eq("Cerrado"), df["Tiempo aviso"], "No aplica"
)
df["Pendiente situación"] = np.where(
    df["Estado aviso"].eq("Abierto"),
    np.where(df["Tiempo aviso"].eq("Atrasado"), "Pendiente vencido",
             np.where(df["Tiempo aviso"].eq("A tiempo"), "Pendiente dentro del plazo", "Pendiente sin clasificación")),
    "No aplica"
)
df["Días restantes/vencidos"] = pd.to_numeric(df["Cumple prioridad días"], errors="coerce")

YEARS = sorted(df["Año"].dropna().astype(int).unique().tolist())
MONTHS = [
    (1,"Enero"),(2,"Febrero"),(3,"Marzo"),(4,"Abril"),(5,"Mayo"),(6,"Junio"),
    (7,"Julio"),(8,"Agosto"),(9,"Septiembre"),(10,"Octubre"),(11,"Noviembre"),(12,"Diciembre")
]
MONTH_LABEL = {n: label for n,label in MONTHS}

def fmt_int(v):
    try: return f"{int(round(float(v))):,}".replace(",", ".")
    except Exception: return "0"

def fmt_pct(v):
    try: return f"{float(v):.1f}%".replace(".", ",")
    except Exception: return "0,0%"

def options(col):
    vals = sorted(df[col].dropna().astype(str).unique().tolist())
    return [{"label": x, "value": x} for x in vals if x and x != "Sin dato"]

def base_layout(fig, height=310, legend=True):
    fig.update_layout(
        height=height, autosize=True,
        margin=dict(l=14, r=14, t=20, b=48),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="DM Sans, Arial, sans-serif", color=TEXT, size=13),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="left", x=0, font=dict(size=12, color=TEXT)),
        hoverlabel=dict(font=dict(family="DM Sans, Arial, sans-serif", size=13))
    )
    fig.update_xaxes(showgrid=False, zeroline=False, automargin=True,
                     tickfont=dict(size=12, color=TEXT), title_font=dict(size=13, color=TEXT))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, automargin=True,
                     tickfont=dict(size=12, color=TEXT), title_font=dict(size=13, color=TEXT))
    # Aumenta la legibilidad de las etiquetas numéricas presentes en las gráficas.
    for trace in fig.data:
        if getattr(trace, "text", None) is not None:
            try:
                trace.textfont = dict(size=12, color=TEXT)
            except Exception:
                pass
    for ann in fig.layout.annotations or []:
        if ann.font is None or ann.font.size is None or ann.font.size < 13:
            ann.font = dict(size=14, color=NAVY)
    return fig

def empty_fig(msg="No hay datos para los filtros seleccionados"):
    fig=go.Figure()
    fig.add_annotation(text=msg,x=.5,y=.5,xref="paper",yref="paper",showarrow=False,
                       font=dict(size=13,color=MUTED))
    fig.update_xaxes(visible=False); fig.update_yaxes(visible=False)
    return base_layout(fig,260,False)

def kpi(label,value,detail="",kind="info"):
    return html.Div([
        html.Div(label,className="kpi-label"),
        html.Div(value,className="kpi-value"),
        html.Div(detail,className="kpi-delta")
    ],className=f"kpi-card {kind}")

def card(title,fig,summary=""):
    return html.Div([
        html.Div(title,className="chart-title"),
        dcc.Graph(figure=fig,config={"displayModeBar":False,"responsive":True}),
        html.Div(summary,className="chart-subtitle") if summary else None
    ],className="chart-card")

def header(title,subtitle):
    return html.Div([html.Div(title,className="page-title"),
                     html.Div(subtitle,className="page-subtitle")],className="page-header")

def filter_data(years=None, types=None, depts=None):
    d=df.copy()
    if years: d=d[d["Año"].isin(years)]
    if depts: d=d[d["Departamento"].isin(depts)]
    if types: d=d[d["Tipo de aviso"].isin(types)]
    return d

def kpis(d):
    closed=d[d["Estado aviso"].eq("Cerrado")]
    opened=d[d["Estado aviso"].eq("Abierto")]
    ontime=int(closed["Tiempo aviso"].eq("A tiempo").sum())
    late=int(closed["Tiempo aviso"].eq("Atrasado").sum())
    pending_late=int(opened["Tiempo aviso"].eq("Atrasado").sum())
    pending_ontime=int(opened["Tiempo aviso"].eq("A tiempo").sum())
    rate=ontime/(ontime+late)*100 if ontime+late else 0
    return [
        kpi("AVISOS REGISTRADOS",fmt_int(len(d)),"Base filtrada · marca normal","info"),
        kpi("AVISOS CERRADOS",fmt_int(len(closed)),f"{len(closed)/len(d)*100:.1f}% del total" if len(d) else "0%","ok"),
        kpi("AVISOS PENDIENTES",fmt_int(len(opened)),f"{pending_late} vencidos · {pending_ontime} dentro del plazo","warning"),
        kpi("CUMPLIMIENTO EN CERRADOS",fmt_pct(rate),f"{ontime} a tiempo de {ontime+late} cerrados","ok" if rate>=80 else "warning"),
        kpi("PENDIENTES VENCIDOS",fmt_int(pending_late),f"{pending_late/len(opened)*100:.1f}% de abiertos" if len(opened) else "0%","danger")
    ]

def status_donut(d):
    c=d["Estado aviso"].value_counts().rename_axis("Estado").reset_index(name="Avisos")
    if c.empty: return empty_fig()
    colors={"Cerrado":BLUE,"Abierto":RED}
    fig=go.Figure(go.Pie(
        labels=c["Estado"],values=c["Avisos"],hole=.60,
        marker=dict(colors=[colors.get(x,AMBER) for x in c["Estado"]],line=dict(color="white",width=3)),
        textinfo="label+percent",textposition="outside",
        textfont=dict(size=14,color=TEXT),
        hovertemplate="<b>%{label}</b><br>Avisos: %{value:,}<br>Participación: %{percent}<extra></extra>"
    ))
    fig.add_annotation(text=f"<b>{fmt_int(len(d))}</b><br><span style='font-size:13px;color:{MUTED}'>Avisos</span>",
                       x=.5,y=.5,showarrow=False,font=dict(color=NAVY,size=17))
    return base_layout(fig,315,False)

def closed_compliance_donut(d):
    c=d[d["Estado aviso"].eq("Cerrado")]
    v=c["Tiempo aviso"].value_counts().reindex(["A tiempo","Atrasado"],fill_value=0)
    if v.sum()==0: return empty_fig()
    rate=v["A tiempo"]/v.sum()*100
    fig=go.Figure(go.Pie(
        labels=v.index,values=v.values,hole=.60,
        marker=dict(colors=[BLUE,RED],line=dict(color="white",width=3)),
        textinfo="label+percent",textposition="outside",
        textfont=dict(size=14,color=TEXT),
        hovertemplate="<b>%{label}</b><br>Avisos: %{value:,}<br>Participación: %{percent}<extra></extra>"
    ))
    fig.add_annotation(text=f"<b>{rate:.1f}%</b><br><span style='font-size:13px;color:{MUTED}'>A tiempo</span>",
                       x=.5,y=.5,showarrow=False,font=dict(color=NAVY,size=17))
    return base_layout(fig,315,False)

def trend_incoming_closed(d):
    if d.empty: return empty_fig()
    a=d.groupby(d["Fecha de aviso"].dt.to_period("M").dt.to_timestamp()).size().rename("Recibidos")
    c=d[d["Estado aviso"].eq("Cerrado")].groupby(d.loc[d["Estado aviso"].eq("Cerrado"),"Mes cierre fecha"]).size().rename("Cerrados")
    g=pd.concat([a,c],axis=1).fillna(0).reset_index().rename(columns={"index":"Mes"})
    xcol=g.columns[0]
    fig=go.Figure()
    fig.add_trace(go.Scatter(x=g[xcol],y=g["Recibidos"],name="Avisos recibidos",mode="lines",
                             line=dict(color=CYAN,width=2.5)))
    fig.add_trace(go.Scatter(x=g[xcol],y=g["Cerrados"],name="Avisos cerrados",mode="lines",
                             line=dict(color=GREEN,width=2.5)))
    fig.update_layout(xaxis_title="Mes",yaxis_title="Cantidad de avisos")
    return base_layout(fig,330,True)

def annual_backlog(d):
    """Barras agrupadas anuales con el mismo estilo ejecutivo del dashboard ENERGY."""
    if d.empty:
        return empty_fig()

    # Crear las dos categorías de estado para cada año, incluso cuando una
    # categoría tenga cero avisos, y ordenar los años cronológicamente.
    g = (
        d.groupby(["Año", "Estado aviso"], observed=False)
         .size()
         .reset_index(name="Avisos")
    )
    years = sorted(pd.to_numeric(d["Año"], errors="coerce").dropna().astype(int).unique().tolist())
    states = ["Cerrado", "Abierto"]
    full_index = pd.MultiIndex.from_product(
        [years, states], names=["Año", "Estado aviso"]
    )
    g = (
        g.set_index(["Año", "Estado aviso"])
         .reindex(full_index, fill_value=0)
         .reset_index()
    )
    g["Año etiqueta"] = g["Año"].astype(int).astype(str)
    year_order = [str(y) for y in years]
    g["Estado aviso"] = pd.Categorical(
        g["Estado aviso"], categories=states, ordered=True
    )
    g = g.sort_values(["Año", "Estado aviso"])

    # Se reutiliza el mismo patrón Plotly del gráfico de referencia:
    # px.bar agrupado, colores de estado, esquinas redondeadas y etiquetas.
    fig = px.bar(
        g,
        x="Año etiqueta",
        y="Avisos",
        color="Estado aviso",
        barmode="group",
        text="Avisos",
        category_orders={
            "Año etiqueta": year_order,
            "Estado aviso": states,
        },
        color_discrete_map=STATUS_COLORS,
    )

    for tr in fig.data:
        tr.texttemplate = "%{y:,}"
        tr.textposition = "outside"
        tr.cliponaxis = False
        tr.textfont = dict(
            family="DM Sans, Arial, sans-serif",
            size=11,
            color=TEXT,
        )
        tr.marker.cornerradius = 7
        tr.marker.line.width = 0
        tr.hovertemplate = (
            "<b>Año %{x}</b><br>%{fullData.name}: %{y:,}<extra></extra>"
        )

    max_value = int(g["Avisos"].max()) if len(g) else 0
    fig.update_layout(
        barmode="group",
        bargap=0.16,
        bargroupgap=0.035,
        uniformtext_minsize=9,
        uniformtext_mode="hide",
        legend=dict(
            orientation="h",
            y=1.06,
            x=0,
            xanchor="left",
        ),
        margin=dict(l=46, r=20, t=40, b=58),
    )
    fig.update_xaxes(
        title="Año de aviso",
        tickangle=0,
        showgrid=False,
        automargin=True,
        tickmode="array",
        tickvals=year_order,
        ticktext=year_order,
        tickfont=dict(
            family="DM Sans, Arial, sans-serif",
            size=10,
        ),
    )
    fig.update_yaxes(
        title="Número de avisos",
        gridcolor=GRID,
        zeroline=False,
        range=[0, max_value * 1.28 if max_value else 1],
        showticklabels=False,
        tickfont=dict(
            family="DM Sans, Arial, sans-serif",
            size=10,
        ),
    )
    return base_layout(fig, 350, True)


def compliance_by_priority(d):
    c=d[d["Estado aviso"].eq("Cerrado")]
    if c.empty:
        return empty_fig()
    g=c.groupby("Prioridad").agg(
        Total=("Aviso","nunique"),
        A_tiempo=("Tiempo aviso",lambda s:int(s.eq("A tiempo").sum()))
    ).reset_index()
    g["Cumplimiento"]=g["A_tiempo"]/g["Total"]*100
    order=["Mes","Trimestre","Semestre","Año","Dos años","Tres años","Seis años"]
    g["ord"]=g["Prioridad"].apply(lambda x:order.index(x) if x in order else 99)
    g=g.sort_values("ord")

    fig=px.bar(
        g,x="Prioridad",y="Cumplimiento",
        text=g["Cumplimiento"].map(lambda x:f"{x:.1f}%"),
        color="Cumplimiento",
        color_continuous_scale=[[0,RED],[.5,AMBER],[1,GREEN]],
        hover_data={"Total":True,"A_tiempo":True,"Cumplimiento":":.1f","ord":False}
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(family="DM Sans, Arial, sans-serif",size=12,color=TEXT),
        cliponaxis=False,
        marker=dict(cornerradius=7,line=dict(width=0))
    )
    fig.update_layout(
        coloraxis_showscale=False,
        yaxis_title="% de cerrados a tiempo",
        xaxis_title="Prioridad",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        margin=dict(l=46,r=24,t=28,b=52)
    )
    fig.update_xaxes(tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT))
    fig.update_yaxes(range=[0,112],dtick=20,tickfont=dict(size=11,color=TEXT))
    return base_layout(fig,330,False)


def monthly_closed_compliance(d):
    c=d[d["Estado aviso"].eq("Cerrado")].copy()
    if c.empty:
        return empty_fig()
    c["Mes cierre"] = c["Fecha de cierre"].dt.to_period("M").dt.to_timestamp()
    g=c.groupby("Mes cierre").agg(
        Cerrados=("Aviso","nunique"),
        A_tiempo=("Tiempo aviso",lambda s:int(s.eq("A tiempo").sum()))
    ).reset_index()
    g["Cumplimiento"] = g["A_tiempo"]/g["Cerrados"]*100

    fig=go.Figure()
    fig.add_trace(go.Scatter(
        x=g["Mes cierre"],y=g["Cumplimiento"],
        mode="lines+markers",
        name="Cumplimiento mensual",
        line=dict(color=BLUE,width=3),
        marker=dict(
            color=CYAN,
            size=7,
            line=dict(color=BLUE,width=1)
        ),
        customdata=g[["Cerrados","A_tiempo"]],
        hovertemplate=(
            "<b>%{x|%B %Y}</b><br>"
            "Cumplimiento: %{y:.1f}%<br>"
            "Avisos cerrados: %{customdata[0]:,}<br>"
            "Cerrados a tiempo: %{customdata[1]:,}<extra></extra>"
        )
    ))
    fig.add_hline(
        y=100,line_dash="dot",line_color=GREEN,opacity=.75,
        annotation_text="Meta: 100%",annotation_position="top left"
    )
    fig.update_yaxes(
        range=[0,110],
        dtick=20,
        title="% de avisos cerrados a tiempo",
        tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT)
    )
    fig.update_xaxes(
        title="Mes de cierre",
        tickformat="%Y",
        dtick="M12",
        tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT)
    )
    fig.update_layout(
        margin=dict(l=58,r=28,t=42,b=58),
        hovermode="x unified"
    )
    return base_layout(fig,390,False)


def late_by_type(d):
    c=d[d["Estado aviso"].eq("Cerrado")]
    if c.empty:
        return empty_fig()
    g=c.groupby("Tipo de aviso").agg(
        Total=("Aviso","nunique"),
        Atrasados=("Tiempo aviso",lambda s:int(s.eq("Atrasado").sum()))
    ).reset_index()
    g["% atrasados"]=g["Atrasados"]/g["Total"]*100
    g=g.sort_values("% atrasados",ascending=True)

    fig=px.bar(
        g,x="% atrasados",y="Tipo de aviso",orientation="h",
        text=g["% atrasados"].map(lambda x:f"{x:.1f}%"),
        color="% atrasados",
        color_continuous_scale=[[0,GREEN],[.5,AMBER],[1,RED]],
        hover_data={"Total":True,"Atrasados":True,"% atrasados":":.1f"}
    )
    fig.update_traces(
        textposition="outside",
        textfont=dict(family="DM Sans, Arial, sans-serif",size=12,color=TEXT),
        cliponaxis=False,
        marker=dict(cornerradius=7,line=dict(width=0))
    )
    max_value=float(g["% atrasados"].max()) if len(g) else 0
    fig.update_layout(
        coloraxis_showscale=False,
        xaxis_title="% de avisos cerrados atrasados",
        yaxis_title="",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        margin=dict(l=150,r=48,t=24,b=48)
    )
    fig.update_xaxes(range=[0,max_value*1.18 if max_value else 1],
                     tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT))
    fig.update_yaxes(tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT))
    return base_layout(fig,350,False)


def pending_status(d):
    o=d[d["Estado aviso"].eq("Abierto")]
    states=[
        "Pendiente dentro del plazo",
        "Pendiente vencido",
        "Pendiente sin clasificación"
    ]
    vals=o["Pendiente situación"].value_counts().reindex(states,fill_value=0)
    if vals.sum()==0:
        return empty_fig()

    # Colores semánticos de theme.py: cumplimiento, atraso y advertencia.
    status_colors=[GREEN,RED,AMBER]
    fig=go.Figure(go.Pie(
        labels=vals.index,
        values=vals.values,
        hole=.58,
        marker=dict(colors=status_colors,line=dict(color="white",width=3)),
        textinfo="label+value+percent",
        textposition="outside",
        textfont=dict(family="DM Sans, Arial, sans-serif",size=12,color=TEXT),
        hovertemplate="<b>%{label}</b><br>Avisos: %{value:,}<br>Participación: %{percent}<extra></extra>"
    ))
    fig.add_annotation(
        text=f"<b>{fmt_int(len(o))}</b><br><span style='font-size:12px;color:{MUTED}'>Pendientes</span>",
        x=.5,y=.5,showarrow=False,font=dict(color=NAVY,size=17)
    )
    return base_layout(fig,320,False)



def pending_age(d):
    o=d[d["Estado aviso"].eq("Abierto")].copy()
    if o.empty:
        return empty_fig()
    bins=[-1,90,365,730,1460,10000]
    labels=["0–90 días","91–365 días","1–2 años","2–4 años","Más de 4 años"]
    o["Antigüedad"]=pd.cut(o["Días abierto"],bins=bins,labels=labels)
    g=o["Antigüedad"].value_counts().reindex(labels,fill_value=0).reset_index()
    g.columns=["Antigüedad","Avisos"]

    # Secuencia de la paleta ENERGY: tonos azules para menor antigüedad,
    # ámbar para antigüedad intermedia y rojo/azul profundo para mayor riesgo.
    age_colors={
        "0–90 días":CYAN,
        "91–365 días":BLUE_2,
        "1–2 años":AMBER,
        "2–4 años":RED,
        "Más de 4 años":NAVY
    }
    fig=px.bar(
        g,x="Antigüedad",y="Avisos",text="Avisos",
        color="Antigüedad",
        color_discrete_map=age_colors,
        category_orders={"Antigüedad":labels}
    )
    fig.update_traces(
        texttemplate="%{y:,}",
        textposition="outside",
        textfont=dict(family="DM Sans, Arial, sans-serif",size=12,color=TEXT),
        cliponaxis=False,
        marker=dict(cornerradius=7,line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>Avisos abiertos: %{y:,}<extra></extra>"
    )
    max_value=int(g["Avisos"].max()) if len(g) else 0
    fig.update_layout(
        showlegend=False,
        xaxis_title="Antigüedad del pendiente",
        yaxis_title="Avisos",
        uniformtext_minsize=10,
        uniformtext_mode="hide",
        margin=dict(l=48,r=22,t=28,b=54)
    )
    fig.update_yaxes(range=[0,max_value*1.20 if max_value else 1],dtick=50)
    fig.update_xaxes(tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT))
    return base_layout(fig,320,False)



def pending_by_type(d):
    o=d[d["Estado aviso"].eq("Abierto")]
    if o.empty:
        return empty_fig()
    states=[
        "Pendiente dentro del plazo",
        "Pendiente vencido",
        "Pendiente sin clasificación"
    ]
    types_order=["Construcciones","Invasión/Explanacion","Obras","Permiso Ingreso","Vegetación"]
    g=o.groupby(["Tipo de aviso","Pendiente situación"]).size().reset_index(name="Avisos")
    fig=px.bar(
        g,x="Tipo de aviso",y="Avisos",
        color="Pendiente situación",
        barmode="stack",
        category_orders={
            "Pendiente situación":states,
            "Tipo de aviso":types_order
        },
        color_discrete_map={
            "Pendiente dentro del plazo":GREEN,
            "Pendiente vencido":RED,
            "Pendiente sin clasificación":AMBER
        }
    )
    fig.update_layout(
        xaxis_title="Tipo de aviso",
        yaxis_title="Avisos",
        legend_title_text="Situación del pendiente"
    )
    fig.update_xaxes(tickfont=dict(family="DM Sans, Arial, sans-serif",size=11,color=TEXT))
    return base_layout(fig,320,True)



def department_performance(d):
    c=d[d["Estado aviso"].eq("Cerrado")]
    o=d[d["Estado aviso"].eq("Abierto")]
    if d.empty:
        return empty_fig()

    pending=o.groupby("Departamento").size().rename("Pendientes")
    late=c[c["Tiempo aviso"].eq("Atrasado")].groupby("Departamento").size().rename("Cerrados atrasados")
    g=pd.concat([pending,late],axis=1).fillna(0).reset_index()

    # Excluir registros sin departamento identificado.
    department_text=g["Departamento"].fillna("").astype(str).str.strip()
    missing_labels={"","sin dato","s/d","sd","no registra","no disponible","nan","none","null"}
    g=g.loc[~department_text.str.lower().isin(missing_labels)].copy()
    if g.empty:
        return empty_fig("No hay departamentos identificados para los filtros seleccionados.")

    g["Total"]=g["Pendientes"]+g["Cerrados atrasados"]
    # Se muestran los departamentos con mayor volumen combinado; el mayor queda arriba.
    g=g.sort_values("Total",ascending=False,kind="stable").head(12)
    department_order=g["Departamento"].astype(str).tolist()

    fig=go.Figure()
    fig.add_trace(go.Bar(
        y=g["Departamento"],x=g["Pendientes"],name="Pendientes",
        orientation="h",marker=dict(color=RED,cornerradius=7,line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Pendientes: %{x:,}<extra></extra>"
    ))
    fig.add_trace(go.Bar(
        y=g["Departamento"],x=g["Cerrados atrasados"],name="Cerrados atrasados",
        orientation="h",marker=dict(color=AMBER,cornerradius=7,line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Cerrados atrasados: %{x:,}<extra></extra>"
    ))
    fig.update_layout(
        barmode="stack",xaxis_title="Avisos",yaxis_title="",
        bargap=.22,legend=dict(orientation="h",y=1.04,x=0),
        margin=dict(l=120,r=22,t=42,b=48),
        yaxis=dict(
            categoryorder="array",
            categoryarray=department_order,
            autorange="reversed"
        )
    )
    fig.update_xaxes(tickfont=dict(size=11,color=TEXT))
    fig.update_yaxes(tickfont=dict(size=11,color=TEXT))
    return base_layout(fig,370,True)


# GeoJSON nacional de departamentos (MGN 2025 derivado de DANE).
COLOMBIA_DEPARTMENTS_GEOJSON_URL = (
    "https://raw.githubusercontent.com/ytolosa/mapas-colombia/main/"
    "output/geojson/col_departamentos_inset_nacional.geojson"
)
_COLOMBIA_GEOJSON_CACHE = None

def load_colombia_departments_geojson():
    global _COLOMBIA_GEOJSON_CACHE
    if _COLOMBIA_GEOJSON_CACHE is not None:
        return _COLOMBIA_GEOJSON_CACHE
    try:
        import urllib.request
        req=urllib.request.Request(
            COLOMBIA_DEPARTMENTS_GEOJSON_URL,
            headers={"User-Agent":"Dashboard-Avisos-Equipo2/1.7"}
        )
        with urllib.request.urlopen(req,timeout=8) as response:
            _COLOMBIA_GEOJSON_CACHE=json.loads(response.read().decode("utf-8"))
    except Exception:
        _COLOMBIA_GEOJSON_CACHE={}
    return _COLOMBIA_GEOJSON_CACHE

DEPARTMENT_CAPITALS = [
    ("Amazonas","Leticia",-4.2153,-69.9406),("Antioquia","Medellín",6.2442,-75.5812),
    ("Arauca","Arauca",7.0847,-70.7591),("Atlántico","Barranquilla",10.9685,-74.7813),
    ("Bogotá, D.C.","Bogotá",4.7110,-74.0721),("Bolívar","Cartagena",10.3910,-75.4794),
    ("Boyacá","Tunja",5.5353,-73.3678),("Caldas","Manizales",5.0703,-75.5138),
    ("Caquetá","Florencia",1.6144,-75.6062),("Casanare","Yopal",5.3378,-72.3959),
    ("Cauca","Popayán",2.4448,-76.6147),("Cesar","Valledupar",10.4631,-73.2532),
    ("Chocó","Quibdó",5.6947,-76.6611),("Córdoba","Montería",8.7480,-75.8814),
    ("Cundinamarca","Bogotá",4.7110,-74.0721),("Guainía","Inírida",3.8653,-67.9239),
    ("Guaviare","San José del Guaviare",2.5729,-72.6459),("Huila","Neiva",2.9273,-75.2819),
    ("La Guajira","Riohacha",11.5444,-72.9072),("Magdalena","Santa Marta",11.2408,-74.1990),
    ("Meta","Villavicencio",4.1420,-73.6266),("Nariño","Pasto",1.2136,-77.2811),
    ("Norte de Santander","Cúcuta",7.8891,-72.4967),("Putumayo","Mocoa",1.1493,-76.6470),
    ("Quindío","Armenia",4.5339,-75.6811),("Risaralda","Pereira",4.8087,-75.6906),
    ("San Andrés y Providencia","San Andrés",12.5847,-81.7006),("Santander","Bucaramanga",7.1193,-73.1227),
    ("Sucre","Sincelejo",9.3047,-75.3978),("Tolima","Ibagué",4.4389,-75.2322),
    ("Valle del Cauca","Cali",3.4516,-76.5320),("Vaupés","Mitú",1.2530,-70.2340),
    ("Vichada","Puerto Carreño",6.1890,-67.4859),
]

def geo_map(d):
    """Mapa interactivo de relieve, vías, municipios analizados y capitales."""
    try:
        import folium
        from branca.element import Element
    except ImportError:
        return html.Div(
            "Para visualizar el mapa topográfico instala las dependencias de requirements.txt.",
            className="table-empty"
        )

    g=d.dropna(subset=["Latitud","Longitud"]).copy()
    if g.empty:
        return html.Div("No hay coordenadas para mostrar.",className="table-empty")

    g["Ubicación"]=g["Municipio"].astype(str)+", "+g["Departamento"].astype(str)
    agg=g.groupby(["Ubicación","Municipio","Departamento","Latitud","Longitud"]).agg(
        Avisos=("Aviso","nunique"),
        Pendientes=("Estado aviso",lambda s:int(s.eq("Abierto").sum())),
        Atrasados=("Tiempo aviso",lambda s:int(s.eq("Atrasado").sum()))
    ).reset_index()
    agg["% pendientes"]=np.where(agg["Avisos"]>0,agg["Pendientes"]/agg["Avisos"]*100,0)

    caps=pd.DataFrame(
        DEPARTMENT_CAPITALS,
        columns=["Departamento","Capital","Latitud","Longitud"]
    )

    # Encuadre de Colombia con cobertura de municipios y capitales.
    all_lat=list(agg["Latitud"].astype(float))+list(caps["Latitud"].astype(float))
    all_lon=list(agg["Longitud"].astype(float))+list(caps["Longitud"].astype(float))
    bounds=[[min(all_lat)-.6,min(all_lon)-.6],[max(all_lat)+.6,max(all_lon)+.6]]

    m=folium.Map(
        location=[4.2,-73.8],
        zoom_start=5,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
        zoom_control=True,
        width="100%",
        height="370px"
    )

    # Mapa topográfico: incluye relieve, hidrografía, ciudades y red vial.
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles © Esri — Sources: Esri, HERE, Garmin, USGS, Intermap, INCREMENT P, NRCAN, Esri Japan, METI, Esri China (Hong Kong), OpenStreetMap contributors, and the GIS User Community",
        name="Relieve y vías",
        overlay=False,
        control=True,
        show=True
    ).add_to(m)

    # Alternativa con detalle de calles y caminos basada en OpenStreetMap.
    folium.TileLayer(
        tiles="OpenStreetMap",
        name="Calles y caminos",
        overlay=False,
        control=True,
        show=False
    ).add_to(m)

    # Límites departamentales del GeoJSON de referencia, si están disponibles.
    geojson=load_colombia_departments_geojson()
    if isinstance(geojson,dict) and geojson.get("features"):
        folium.GeoJson(
            geojson,
            name="Límites departamentales",
            style_function=lambda feature:{
                "color":"#8FA6C5","weight":1.0,"opacity":.85,
                "fillColor":"#EAF0F8","fillOpacity":.08
            },
            tooltip=folium.GeoJsonTooltip(
                fields=list(geojson["features"][0].get("properties",{}).keys())[:1],
                aliases=["Departamento:"],
                sticky=True
            ) if geojson["features"][0].get("properties") else None,
            show=True
        ).add_to(m)

    # Municipios: tamaño por volumen y color por porcentaje pendiente.
    def _pending_color(value):
        if value < 33.333:
            return GREEN
        if value < 66.667:
            return AMBER
        return RED

    municipality_group=folium.FeatureGroup(name="Municipios analizados",show=True)
    for _,r in agg.iterrows():
        # Escala de tamaño no lineal para que diferencias de volumen sean perceptibles.
        # 1 aviso = 4 px; 2 avisos ≈ 8.5 px; 12 avisos ≈ 18 px.
        radius=float(np.clip(4+np.sqrt(max(float(r["Avisos"])-1,0))*4.1,4,18))
        color=_pending_color(float(r["% pendientes"]))
        popup=(
            f"<b>{r['Ubicación']}</b><br>"
            f"Avisos: {fmt_int(r['Avisos'])}<br>"
            f"Pendientes: {fmt_int(r['Pendientes'])}<br>"
            f"Cerrados atrasados: {fmt_int(r['Atrasados'])}<br>"
            f"Porcentaje pendiente: {r['% pendientes']:.1f}%"
        )
        folium.CircleMarker(
            location=[float(r["Latitud"]),float(r["Longitud"])],
            radius=radius,
            color="#FFFFFF",
            weight=1,
            fill=True,
            fill_color=color,
            fill_opacity=.92,
            tooltip=f"{r['Municipio']}, {r['Departamento']} · {r['% pendientes']:.1f}% pendiente",
            popup=folium.Popup(popup,max_width=260)
        ).add_to(municipality_group)
    municipality_group.add_to(m)

    # Capitales departamentales: punto azul discreto y nombre, sin iconografía de estrella.
    capital_group=folium.FeatureGroup(name="Capitales departamentales",show=True)
    for _,r in caps.iterrows():
        capital_icon=folium.DivIcon(
            html=(
                '<div style="display:flex;align-items:center;gap:3px;'
                'white-space:nowrap;pointer-events:auto;'
                'font:9px Arial,sans-serif;color:#17345F;'
                'text-shadow:1px 1px 2px #fff,-1px -1px 2px #fff;">'
                '<span style="display:inline-block;width:5px;height:5px;'
                'border-radius:50%;background:#1F4D9C;'
                'border:1px solid #fff;flex:0 0 5px;"></span>'
                f'<span>{r["Capital"]}</span></div>'
            ),
            icon_size=(100,14),
            icon_anchor=(3,7)
        )
        folium.Marker(
            location=[float(r["Latitud"]),float(r["Longitud"])],
            tooltip=f"{r['Capital']} · Capital de {r['Departamento']}",
            popup=folium.Popup(
                f"<b>{r['Capital']}</b><br>Capital de {r['Departamento']}",
                max_width=220
            ),
            icon=capital_icon
        ).add_to(capital_group)
    capital_group.add_to(m)

    # Controles cartográficos: alternar únicamente las capas de fondo y consulta.
    folium.LayerControl(collapsed=True,position="topright").add_to(m)
    m.fit_bounds(bounds,padding=(12,12))

    # Leyenda compacta para interpretar el porcentaje pendiente sin ocupar una franja superior.
    legend_html=f"""
    <div style="
      position: fixed; bottom: 12px; left: 12px; z-index: 9999;
      background: rgba(255,255,255,.94); border: 1px solid #D1DCEC;
      border-radius: 7px; padding: 7px 9px; font: 11px Arial,sans-serif;
      color: #17345F; box-shadow: 0 1px 5px rgba(0,0,0,.12);">
      <div style="font-weight:700;margin-bottom:5px">% pendiente</div>
      <span style="color:{GREEN}">●</span> 0–33%
      &nbsp; <span style="color:{AMBER}">●</span> 34–66%
      &nbsp; <span style="color:{RED}">●</span> 67–100%
      <div style="font-size:10px;color:#526783;margin-top:4px">
        Tamaño del punto: volumen de avisos
      </div>
    </div>
    """
    m.get_root().html.add_child(Element(legend_html))
    return html.Iframe(
        srcDoc=m.get_root().render(),
        title="Mapa topográfico de Colombia con municipios analizados y capitales",
        style={
            "width":"100%",
            "height":"370px",
            "border":"0",
            "borderRadius":"8px",
            "display":"block"
        }
    )



def municipality_table(d):
    o=d[d["Estado aviso"].eq("Abierto")]
    if o.empty:
        return html.Div("No hay avisos pendientes para los filtros seleccionados.",className="table-empty")
    g=o.groupby(["Departamento","Municipio"]).agg(
       Pendientes=("Aviso","nunique"),
       Vencidos=("Tiempo aviso",lambda s:int(s.eq("Atrasado").sum())),
       Antigüedad_mediana=("Días abierto","median")
    ).reset_index()
    g=g.sort_values(["Vencidos","Pendientes"],ascending=False).head(15)
    head=["Departamento","Municipio","Pendientes","Vencidos","Antigüedad mediana (días)"]
    rows=[html.Tr([html.Th(x) for x in head])]
    for _,r in g.iterrows():
        rows.append(html.Tr([
            html.Td(r["Departamento"]),html.Td(r["Municipio"]),
            html.Td(fmt_int(r["Pendientes"])),html.Td(fmt_int(r["Vencidos"])),
            html.Td(fmt_int(r["Antigüedad_mediana"]))
        ]))
    return html.Div(html.Table(rows,className="data-table territory-table"),className="table-scroll")



def page_resumen(d):
    closed=d[d["Estado aviso"].eq("Cerrado")]
    opened=d[d["Estado aviso"].eq("Abierto")]
    ontime=int(closed["Tiempo aviso"].eq("A tiempo").sum())
    late=int(closed["Tiempo aviso"].eq("Atrasado").sum())
    return html.Div([
      header("Resumen gerencial","Estado general del contrato: avisos registrados, resultados de atención y pendientes por cumplir."),
      html.Div(kpis(d),className="kpi-row"),
      html.Div([
        card("Estado general de los avisos",status_donut(d),
             "Diferencia entre avisos cerrados y avisos que permanecen pendientes."),
        card("Cumplimiento de los avisos cerrados",closed_compliance_donut(d),
             "El porcentaje se calcula exclusivamente sobre avisos cerrados clasificados como 'A tiempo' o 'Atrasado'.")
      ],className="charts-2col"),
      html.Div([
        card("Evolución mensual: avisos recibidos frente a avisos cerrados",trend_incoming_closed(d),
             "La línea azul muestra los avisos recibidos en cada mes y la verde, los avisos que se cerraron en ese mes. Por eso, no necesariamente corresponden a los mismos avisos."),
        card("Volumen histórico y pendientes actuales por año de aviso",annual_backlog(d),
             "Compara los avisos cerrados y los que seguían abiertos por año de recepción. Los abiertos corresponden al inventario pendiente en la fecha de corte de la base.")
      ],className="charts-2col"),
      html.Div([
        html.Div("Lectura ejecutiva",className="chart-title"),
        html.P(f"De {fmt_int(len(d))} avisos, {fmt_int(len(closed))} están cerrados y {fmt_int(len(opened))} siguen abiertos.",className="analysis-item"),
        html.P(f"En los avisos cerrados, {fmt_int(ontime)} se resolvieron a tiempo ({fmt_pct(ontime/(ontime+late)*100 if ontime+late else 0)}) y {fmt_int(late)} se clasificaron como atrasados.",className="analysis-item"),
        html.P(f"De los pendientes, {fmt_int(opened['Tiempo aviso'].eq('Atrasado').sum())} ya aparecen vencidos y {fmt_int(opened['Tiempo aviso'].eq('A tiempo').sum())} permanecen dentro del plazo, según el corte de la base.",className="analysis-item"),
        html.P("La fecha de corte registrada para los avisos abiertos es 6 de mayo de 2023. Los resultados no deben interpretarse como estado actual del contrato.",className="analysis-item")
      ],className="chart-card analysis-card")
    ])

def page_cumplimiento(d):
    return html.Div([
      header("Cumplimiento y plazos","Evaluación de los avisos cerrados frente a los plazos comprometidos, por prioridad y tipo."),
      html.Div(kpis(d),className="kpi-row"),
      html.Div([
        card("Porcentaje de avisos cerrados a tiempo por prioridad",compliance_by_priority(d),
             "Denominador: avisos cerrados de cada prioridad. No incluye avisos abiertos."),
        card("Proporción de avisos cerrados atrasados por tipo",late_by_type(d),
             "Permite localizar tipologías con mayor proporción de incumplimiento entre los avisos ya cerrados.")
      ],className="charts-2col"),
      card("Evolución mensual del cumplimiento de avisos cerrados",monthly_closed_compliance(d),
           "Porcentaje mensual de avisos cerrados a tiempo. Cada punto representa los avisos que se cerraron durante ese mes.")
    ])

def page_pendientes(d):
    o=d[d["Estado aviso"].eq("Abierto")]
    vencidos=int(o["Tiempo aviso"].eq("Atrasado").sum())
    return html.Div([
      header("Pendientes por cumplir","Inventario abierto, vencimientos y antigüedad de los avisos que aún no están cerrados."),
      html.Div([
        kpi("PENDIENTES",fmt_int(len(o)),"Avisos abiertos al corte de la base","warning"),
        kpi("PENDIENTES VENCIDOS",fmt_int(vencidos),f"{vencidos/len(o)*100:.1f}% de los abiertos" if len(o) else "0%","danger"),
        kpi("DENTRO DEL PLAZO",fmt_int(o["Tiempo aviso"].eq("A tiempo").sum()),"Pendientes aún dentro del plazo","ok"),
        kpi("ANTIGÜEDAD MEDIANA",fmt_int(o["Días abierto"].median())+" días","Desde la fecha de aviso","info"),
        kpi("PENDIENTE MÁS ANTIGUO",fmt_int(o["Días abierto"].max())+" días","Antigüedad máxima","warning")
      ],className="kpi-row"),
      html.Div([
        card("Situación de cumplimiento de los pendientes",pending_status(d),
             "Los avisos abiertos se separan entre dentro del plazo y vencidos, usando la clasificación disponible al corte."),
        card("Antigüedad de los avisos abiertos",pending_age(d),
             "Distribución de días transcurridos desde la fecha de aviso hasta la fecha de corte.")
      ],className="charts-2col"),
      card("Pendientes por tipo de aviso y situación frente al plazo",pending_by_type(d),
           "Permite identificar qué tipologías concentran el inventario vencido y el que aún está dentro del plazo."),
      html.Div([
        html.Div("Nota de interpretación",className="chart-title"),
        html.P("Los 596 avisos abiertos tienen fecha de cierre registrada como 06-may-2023, que se interpreta como fecha de corte y no como fecha real de solución.",className="analysis-item"),
        html.P("La etiqueta 'Pendiente vencido' proviene del campo Tiempo aviso. Debe validarse la regla de negocio con el responsable de la fuente antes de convertirla en compromiso contractual definitivo.",className="analysis-item")
      ],className="chart-card analysis-card")
    ])

def page_territorio(d):
    return html.Div([
      header("Territorio y tipologías","Concentración de pendientes y atrasos por departamento, municipio, sector y tipo de aviso."),
      html.Div(kpis(d),className="kpi-row"),
      html.Div([
        html.Div([
          html.Div("Concentración geográfica de avisos y porcentaje pendiente",className="chart-title"),
          geo_map(d),
          html.Div("Mapa topográfico con relieve, ríos y vías. Los puntos representan municipios analizados; el tamaño indica volumen y el color, porcentaje pendiente.",className="chart-subtitle")
        ],className="chart-card territory-map-card"),
        card("Departamentos con mayor concentración de pendientes y cierres atrasados",department_performance(d),
             "Compara avisos pendientes abiertos y avisos cerrados atrasados por departamento.")
      ],className="territory-top-grid"),
      html.Div([
        html.Div("Municipios con mayor acumulación pendiente",className="chart-title"),
        municipality_table(d)
      ],className="chart-card territory-table-card")
    ])



def page_placeholder():
    return build_home()

# Sidebar: identidad, navegación, filtros y autores basados en ENERGY de referencia.
years_opts=[{"label":str(int(y)),"value":int(y)} for y in YEARS]
sidebar=html.Aside([
  html.Div([
    html.Img(src="/assets/logo_energy.png",className="sidebar-logo"),
    html.Div("GESTIÓN DE AVISOS",className="sidebar-brand-caption"),
    html.Div("GRID INTELLIGENCE",className="brand-tag")
  ],className="sidebar-brand"),
  html.Div("NAVEGACIÓN",className="section-label"),
  dcc.Link([html.Span(className="nav-dot"),"Inicio"],href="/inicio",className="nav-link",id="nav-inicio"),
  dcc.Link([html.Span(className="nav-dot"),"Resumen gerencial"],href="/resumen",className="nav-link",id="nav-resumen"),
  dcc.Link([html.Span(className="nav-dot"),"Cumplimiento y plazos"],href="/cumplimiento",className="nav-link",id="nav-cumplimiento"),
  dcc.Link([html.Span(className="nav-dot"),"Pendientes por cumplir"],href="/pendientes",className="nav-link",id="nav-pendientes"),
  dcc.Link([html.Span(className="nav-dot"),"Territorio y tipos"],href="/territorio",className="nav-link",id="nav-territorio"),
  html.Div("FILTROS",className="section-label"),
  html.Div([
    html.Button("↺  RESTABLECER FILTROS",id="reset-filters",n_clicks=0,className="reset-filters-btn"),
    html.Div("BASE ACTIVA · MARCA = NORMAL",className="normal-badge"),
    html.Div("Seleccione uno o varios valores; el tablero se actualiza automáticamente.",className="filter-hint"),
    html.Label("AÑO",className="filter-label"),
    dcc.Dropdown(id="f-year",options=years_opts,value=[],multi=True,clearable=True,searchable=True,placeholder="Todos los años"),
    html.Label("TIPO DE AVISO",className="filter-label"),
    dcc.Dropdown(id="f-type",options=options("Tipo de aviso"),value=[],multi=True,clearable=True,searchable=True,placeholder="Todos los tipos"),
    html.Label("DEPARTAMENTO",className="filter-label"),
    dcc.Dropdown(id="f-dept",options=options("Departamento"),value=[],multi=True,clearable=True,searchable=True,placeholder="Todos los departamentos")
  ],className="sidebar-filters"),
  html.Div([
    html.Div("AUTORES",className="authors-title"),
    html.Div([
      html.Div("MG",className="author-avatar"),
      html.Div("Mauricio Guerrero",className="author-name")
    ],className="author-row"),
    html.Div([
      html.Div("DR",className="author-avatar"),
      html.Div("Daniel Rodriguez",className="author-name")
    ],className="author-row"),
    html.Div([
      html.Div("JB",className="author-avatar"),
      html.Div("Juan Bojacá",className="author-name")
    ],className="author-row"),
    html.Div([
      html.Div("AN",className="author-avatar"),
      html.Div("Andres Nova",className="author-name")
    ],className="author-row")
  ],className="authors-panel")
],id="sidebar",className="sidebar")

app.layout=html.Div([
  dcc.Location(id="url",refresh=False),
  sidebar,
  html.Main([
    html.Button("☰  Filtros",id="mobile-sidebar-toggle",n_clicks=0,className="mobile-sidebar-toggle"),
    html.Div(id="page-content")
  ],className="main-content")
],className="app-wrapper")

@app.callback(
  Output("f-year","value"),Output("f-type","value"),Output("f-dept","value"),
  Input("reset-filters","n_clicks"),prevent_initial_call=True)
def reset_filters(_):
    return [],[],[]

@app.callback(
  Output("page-content","children"),
  Input("url","pathname"),Input("f-year","value"),Input("f-type","value"),Input("f-dept","value"))
def render_page(pathname,years,types,depts):
    d=filter_data(years,types,depts)
    path=pathname or "/inicio"
    if path=="/cumplimiento": return page_cumplimiento(d)
    if path=="/pendientes": return page_pendientes(d)
    if path=="/territorio": return page_territorio(d)
    if path=="/resumen": return page_resumen(d)
    return page_placeholder()

@app.callback(
  Output("nav-inicio","className"),Output("nav-resumen","className"),
  Output("nav-cumplimiento","className"),Output("nav-pendientes","className"),
  Output("nav-territorio","className"),
  Input("url","pathname"))
def active_nav(path):
    p=path or "/inicio"
    paths=["/inicio","/resumen","/cumplimiento","/pendientes","/territorio"]
    return tuple("nav-link active" if p==x else "nav-link" for x in paths)

@app.callback(
  Output("sidebar","className"),Input("mobile-sidebar-toggle","n_clicks"))
def toggle_sidebar(n):
    return "sidebar mobile-open" if n and n%2==1 else "sidebar"

if __name__=="__main__":
    app.run(debug=True,host="127.0.0.1",port=int(os.environ.get("PORT",8050)))
