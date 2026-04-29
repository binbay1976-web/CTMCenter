from flask import Flask, request, render_template_string
import math
import base64
import io
import json
import traceback
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

app = Flask(__name__)

# =====================================================================
# CƠ SỞ DỮ LIỆU TỪ tt_rang7.3.py (DÙNG CHO TRỤ & NÓN)
# =====================================================================
GENERAL_MATERIAL_DB = {
    'C45_TH': {'name': 'Thép 45 (Thường hóa)', 'type': 'mem', 'hard_type': 'HB', 'hard_min': 170, 'hard_max': 217, 'options': [{'label': 'S ≤ 100mm', 'sch': 340, 'sb': 600}]},
    'C45_TC': {'name': 'Thép 45 (Tôi cải thiện)', 'type': 'mem', 'hard_type': 'HB', 'hard_min': 192, 'hard_max': 285, 'options': [{'label': 'S > 60mm', 'sch': 450, 'sb': 750}, {'label': 'S ≤ 60mm', 'sch': 580, 'sb': 850}]},
    '40X_TC': {'name': 'Thép 40X (Tôi cải thiện)', 'type': 'mem', 'hard_type': 'HB', 'hard_min': 230, 'hard_max': 280, 'options': [{'label': 'S ≤ 100mm', 'sch': 550, 'sb': 850}, {'label': 'S ≤ 60mm', 'sch': 700, 'sb': 950}]},
    '40XH_TBM': {'name': 'Thép 40XH (Tôi bề mặt)', 'type': 'cung', 'hard_type': 'HRC', 'hard_min': 45, 'hard_max': 55, 'options': [{'label': 'Lõi tôi cải thiện', 'sch': 1400, 'sb': 1600}]},
    '20X_ThC': {'name': 'Thép 20X (Thấm C, Tôi)', 'type': 'cung', 'hard_type': 'HRC', 'hard_min': 56, 'hard_max': 63, 'options': [{'label': 'S ≤ 60mm', 'sch': 400, 'sb': 650}]},
    '18CrMnTi_ThC': {'name': 'Thép 18CrMnTi (Thấm C, Tôi)', 'type': 'cung', 'hard_type': 'HRC', 'hard_min': 58, 'hard_max': 63, 'options': [{'label': 'Tiết diện vừa', 'sch': 850, 'sb': 1100}]}
}

SHLIM_FORMULAS = [
    {'id': 'fH1', 'name': '2.HB + 70 (Thường hóa, Tôi cải thiện)', 'type': 'mem'},
    {'id': 'fH2', 'name': '18.HRC + 150 (Tôi thể tích)', 'type': 'cung'},
    {'id': 'fH3', 'name': '17.HRC + 200 (Tôi bề mặt)', 'type': 'cung'},
    {'id': 'fH4', 'name': '23.HRC (Thấm Cacbon)', 'type': 'cung'}
]

SFLIM_FORMULAS = [
    {'id': 'fF1', 'name': '1.8.HB (Thường hóa, Tôi cải thiện)', 'type': 'mem'},
    {'id': 'fF2', 'name': '550 MPa (Tôi thể tích)', 'type': 'cung'},
    {'id': 'fF3', 'name': '900 MPa (Tôi bề mặt)', 'type': 'cung'},
    {'id': 'fF4', 'name': '750 MPa (Thấm cacbon thép không Mo)', 'type': 'cung'}
]

TABLE_SOFT_KHB = [
    [0.2, 1.08, 1.05, 1.02, 1.01, 1.01, 1.00, 1.00], [0.4, 1.18, 1.12, 1.05, 1.03, 1.02, 1.01, 1.01],
    [0.6, 1.31, 1.19, 1.07, 1.05, 1.03, 1.02, 1.02], [0.8, 1.45, 1.27, 1.12, 1.08, 1.05, 1.03, 1.02],
    [1.0, None, 1.32, 1.23, 1.16, 1.10, 1.05, 1.03], [1.2, None, 1.43, 1.27, 1.20, 1.14, 1.06, 1.04],
    [1.4, None, None, 1.31, 1.22, 1.16, 1.08, 1.05], [1.6, None, None, 1.38, 1.28, 1.19, 1.12, 1.06]
]
TABLE_SOFT_KFB = [
    [0.2, 1.18, 1.10, 1.05, 1.03, 1.02, 1.01, 1.00], [0.4, 1.38, 1.21, 1.11, 1.06, 1.05, 1.03, 1.01],
    [0.6, 1.61, 1.39, 1.17, 1.12, 1.08, 1.05, 1.02], [0.8, 1.95, 1.58, 1.24, 1.17, 1.12, 1.07, 1.03],
    [1.0, None, 1.78, 1.32, 1.23, 1.16, 1.10, 1.05], [1.2, None, 1.98, 1.41, 1.30, 1.22, 1.14, 1.07],
    [1.4, None, None, 1.51, 1.38, 1.28, 1.19, 1.12], [1.6, None, None, 1.61, 1.45, 1.37, 1.26, 1.15]
]
TABLE_HARD_KHB = [
    [0.2, 1.22, 1.10, 1.05, 1.04, 1.02, 1.01, 1.00], [0.4, 1.44, 1.25, 1.12, 1.08, 1.05, 1.02, 1.01],
    [0.6, None, 1.45, 1.20, 1.14, 1.08, 1.04, 1.02], [0.8, None, 1.65, 1.28, 1.20, 1.14, 1.07, 1.03],
    [1.0, None, None, 1.37, 1.27, 1.19, 1.12, 1.06], [1.2, None, None, 1.47, 1.35, 1.25, 1.16, 1.08]
]
TABLE_HARD_KFB = [
    [0.2, 1.30, 1.20, 1.08, 1.04, 1.03, 1.02, 1.00], [0.4, 1.69, 1.42, 1.18, 1.06, 1.10, 1.04, 1.01],
    [0.6, None, 1.71, 1.30, 1.17, 1.12, 1.08, 1.03], [0.8, None, 1.95, 1.43, 1.27, 1.20, 1.14, 1.06],
    [1.0, None, None, 1.57, 1.39, 1.28, 1.20, 1.11], [1.2, None, None, 1.72, 1.53, 1.41, 1.30, 1.15]
]

# =====================================================================
# CƠ SỞ DỮ LIỆU TỪ tt_ranght4.py (DÙNG CHO HÀNH TINH CHI TIẾT)
# =====================================================================
HT_MATERIAL_DB = {
    '40': {'name': 'Thép 40', 'type': 'HB', 'h_min': 192, 'h_max': 228, 'options': [
        {'label': 'Tôi cải thiện S≤60', 'sb': 700, 'sch': 400}
    ]},
    '45': {'name': 'Thép 45', 'type': 'HB', 'h_min': 170, 'h_max': 285, 'options': [
        {'label': 'Thường hóa S≤80 (HB 170-217)', 'sb': 600, 'sch': 340},
        {'label': 'Tôi cải thiện S≤100 (HB 192-240)', 'sb': 750, 'sch': 450},
        {'label': 'Tôi cải thiện S≤60 (HB 241-285)', 'sb': 850, 'sch': 580}
    ]},
    '50': {'name': 'Thép 50', 'type': 'HB', 'h_min': 179, 'h_max': 255, 'options': [
        {'label': 'Thường hóa S≤80 (HB 179-228)', 'sb': 640, 'sch': 350},
        {'label': 'Tôi cải thiện S≤80 (HB 228-255)', 'sb': 750, 'sch': 530}
    ]},
    '40X': {'name': 'Thép 40X', 'type': 'HB', 'h_min': 230, 'h_max': 280, 'options': [
        {'label': 'Tôi cải thiện S≤100 (HB 230-260)', 'sb': 850, 'sch': 550},
        {'label': 'Tôi cải thiện S≤60 (HB 260-280)', 'sb': 950, 'sch': 700}
    ]},
    '40X_N': {'name': 'Thép 40X (Thấm nitơ)', 'type': 'HRC', 'h_min': 50, 'h_max': 59, 'options': [
        {'label': 'S≤60', 'sb': 1000, 'sch': 800}
    ]},
    '45X': {'name': 'Thép 45X', 'type': 'HB', 'h_min': 163, 'h_max': 280, 'options': [
        {'label': 'Tôi cải thiện S≤100 (HB 230-280)', 'sb': 850, 'sch': 650},
        {'label': 'Tôi cải thiện S: 100-300 (HB 163-269)', 'sb': 750, 'sch': 500},
        {'label': 'Tôi cải thiện S: 300-500 (HB 163-269)', 'sb': 700, 'sch': 450}
    ]},
    '40XH': {'name': 'Thép 40XH', 'type': 'HB', 'h_min': 230, 'h_max': 300, 'options': [
        {'label': 'Tôi cải thiện S≤100', 'sb': 850, 'sch': 600},
        {'label': 'Tôi cải thiện S: 100-300', 'sb': 800, 'sch': 580}
    ]},
    '40XH_T': {'name': 'Thép 40XH (Tôi HRC)', 'type': 'HRC', 'h_min': 48, 'h_max': 54, 'options': [
        {'label': 'Tôi bề mặt S≤40', 'sb': 1600, 'sch': 1400}
    ]},
    '35XM': {'name': 'Thép 35XM', 'type': 'HB', 'h_min': 241, 'h_max': 280, 'options': [
        {'label': 'Tôi cải thiện S≤100', 'sb': 900, 'sch': 800},
        {'label': 'Tôi cải thiện S≤50', 'sb': 900, 'sch': 800}
    ]},
    '35XM_T': {'name': 'Thép 35XM (Tôi HRC)', 'type': 'HRC', 'h_min': 45, 'h_max': 53, 'options': [
        {'label': 'S≤40', 'sb': 1600, 'sch': 1400}
    ]},
    '20X': {'name': 'Thép 20X', 'type': 'HRC', 'h_min': 46, 'h_max': 53, 'options': [
        {'label': 'Thấm Cacbon S≤60', 'sb': 650, 'sch': 400}
    ]},
    '12XH3A': {'name': 'Thép 12XH3A', 'type': 'HRC', 'h_min': 56, 'h_max': 63, 'options': [
        {'label': 'Thấm Cacbon S≤60', 'sb': 900, 'sch': 700}
    ]},
    '25XGT': {'name': 'Thép 25XГT', 'type': 'HRC', 'h_min': 58, 'h_max': 63, 'options': [
        {'label': 'Thấm Cacbon', 'sb': 1150, 'sch': 950}
    ]},
    '45L': {'name': 'Thép 45Л đúc', 'type': 'HB', 'h_min': 170, 'h_max': 217, 'options': [
        {'label': 'Thường hóa', 'sb': 550, 'sch': 320}
    ]},
    '30XHML': {'name': 'Thép 30XHMЛ đúc', 'type': 'HB', 'h_min': 180, 'h_max': 230, 'options': [
        {'label': 'Thường hóa', 'sb': 700, 'sch': 550}
    ]},
    '40XL': {'name': 'Thép 40XЛ đúc', 'type': 'HB', 'h_min': 180, 'h_max': 230, 'options': [
        {'label': 'Thường hóa', 'sb': 650, 'sch': 500}
    ]},
    '35XML': {'name': 'Thép 35XMЛ đúc', 'type': 'HB', 'h_min': 180, 'h_max': 230, 'options': [
        {'label': 'Thường hóa', 'sb': 700, 'sch': 550}
    ]}
}

HT_STRESS_DB = [
    {'id': 'f1', 'name': 'Thường hóa / Tôi cải thiện (HB)', 'type': 'HB', 'sh': 1.1, 'sf': 1.75, 'sh_f': '2*HB+70', 'sf_f': '1.8*HB'},
    {'id': 'f2', 'name': 'Tôi thể tích (HRC)', 'type': 'HRC', 'sh': 1.15, 'sf': 1.75, 'sh_f': '18*HRC+150', 'sf_f': '550'},
    {'id': 'f3', 'name': 'Tôi bề mặt CĐC (m ≥ 3)', 'type': 'HRC', 'sh': 1.2, 'sf': 1.75, 'sh_f': '17*HRC+200', 'sf_f': '900'},
    {'id': 'f4', 'name': 'Tôi bề mặt CĐC (m < 3)', 'type': 'HRC', 'sh': 1.2, 'sf': 1.75, 'sh_f': '17*HRC+200', 'sf_f': '550'},
    {'id': 'f5', 'name': 'Thấm Nitơ', 'type': 'HRC', 'sh': 1.2, 'sf': 1.75, 'sh_f': '1050', 'sf_f': '12*HRC+30'},
    {'id': 'f6', 'name': 'Thấm Cacbon', 'type': 'HRC', 'sh': 1.2, 'sf': 1.55, 'sh_f': '23*HRC', 'sf_f': '750'},
    {'id': 'f7', 'name': 'Thấm C-N (Có Mo)', 'type': 'HRC', 'sh': 1.2, 'sf': 1.55, 'sh_f': '23*HRC', 'sf_f': '1000'},
]

# =====================================================================
# HÀM BỔ TRỢ CHUNG
# =====================================================================
def hrc_to_hb(hrc):
    if hrc < 35: return hrc * 10 
    mapping = {35:325, 38:355, 40:375, 42:400, 45:425, 48:455, 50:480, 53:515, 55:545, 60:600}
    closest = min(mapping.keys(), key=lambda k: abs(k - hrc))
    return mapping[closest]

def calc_ht_stress(f_id, hard_val):
    rec = next((item for item in HT_STRESS_DB if item["id"] == f_id), None)
    if not rec: rec = HT_STRESS_DB[0] 
    sh_val = eval(rec['sh_f'].replace('HB', str(hard_val)).replace('HRC', str(hard_val)))
    sf_val = eval(rec['sf_f'].replace('HB', str(hard_val)).replace('HRC', str(hard_val)))
    return sh_val, sf_val, rec['sh'], rec['sf']

def get_standard_aw(aw_calc):
    stds = [40, 50, 63, 71, 80, 90, 100, 112, 125, 140, 160, 180, 200, 224, 250, 280, 315, 355, 400]
    for val in stds:
        if val >= aw_calc:
            return val
    return math.ceil(aw_calc / 10) * 10

def get_standard_module(m_calc):
    standard_m = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0]
    for m in standard_m:
        if m >= m_calc: return m
    return standard_m[-1]

def get_YF(zv): return 3.47 + 13.2 / zv

def interpolate_factor(table, psi_bd, col_idx):
    pts = [(row[0], row[col_idx]) for row in table if row[col_idx] is not None]
    if not pts: return 1.0 
    if psi_bd <= pts[0][0]: return pts[0][1]
    if psi_bd >= pts[-1][0]: return pts[-1][1]
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]; x2, y2 = pts[i+1]
        if x1 <= psi_bd <= x2:
            return y1 + (y2 - y1) * (psi_bd - x1) / (x2 - x1)
    return 1.0

def calculate_shlim(formula_id, hard_val):
    if formula_id == 'fH1': return 2 * hard_val + 70
    if formula_id == 'fH2': return 18 * hard_val + 150
    if formula_id == 'fH3': return 17 * hard_val + 200
    return 23 * hard_val if formula_id == 'fH4' else 2 * hard_val + 70

def calculate_sflim(formula_id, hard_val):
    if formula_id == 'fF1': return 1.8 * hard_val
    if formula_id == 'fF2': return 550
    if formula_id == 'fF3': return 900
    return 750 if formula_id == 'fF4' else 1.8 * hard_val

def draw_gear_schematic(d1, d2, aw, loai_br, mte=None, b=None):
    try:
        plt.close('all')
        plt.figure(figsize=(9, 5))
        ax = plt.gca()
        if loai_br in ['con_thang', 'con_cong']:
            d1_rad = math.atan2(d1, d2)
            L1 = aw * math.cos(d1_rad)
            L2 = aw * math.sin(d1_rad)
            ha = mte if mte else aw/10
            hf = 1.2 * ha
            b_val = b if b else aw*0.3
            k = 1 - b_val/aw
            
            n_up = (-math.sin(d1_rad), math.cos(d1_rad))
            n_dn = (-math.sin(d1_rad), -math.cos(d1_rad))
            A1 = (L1 + ha * n_up[0], L2 + ha * n_up[1])
            A2 = (L1 + ha * n_dn[0], -L2 + ha * n_dn[1])
            A1in = (k * A1[0], k * A1[1])
            A2in = (k * A2[0], k * A2[1])
            back_x1 = A1[0] + 1.5 * ha
            
            poly1 = plt.Polygon([A1in, A1, (back_x1, A1[1]), (back_x1, A2[1]), A2, A2in], color='#3b82f6', alpha=0.3, ec='#1e3a8a', lw=2)
            ax.add_patch(poly1)
            
            m_rt = (math.cos(d1_rad), -math.sin(d1_rad))
            m_lt = (-math.cos(d1_rad), -math.sin(d1_rad))
            B1 = (L1 + ha * m_rt[0], L2 + ha * m_rt[1])
            B2 = (-L1 + ha * m_lt[0], L2 + ha * m_lt[1])
            B1in = (k * B1[0], k * B1[1])
            B2in = (k * B2[0], k * B2[1])
            back_y2 = B1[1] + 1.5 * ha
            
            poly2 = plt.Polygon([B1in, B1, (B1[0], back_y2), (B2[0], back_y2), B2, B2in], color='#ef4444', alpha=0.3, ec='#991b1b', lw=2)
            ax.add_patch(poly2)
            
            if loai_br == 'con_cong':
                for i in range(1, 6):
                    f = i / 6.0
                    pt_top = (A1in[0] + f*(A1[0]-A1in[0]), A1in[1] + f*(A1[1]-A1in[1]))
                    pt_bot = (A2in[0] + f*(A2[0]-A2in[0]), A2in[1] + f*(A2[1]-A2in[1]))
                    cx, cy = [], []
                    for j in range(11):
                        t = j / 10.0
                        bulge = 0.12 * aw * math.sin(t * math.pi)
                        cx.append(pt_top[0] + t*(pt_bot[0] - pt_top[0]) + bulge)
                        cy.append(pt_top[1] + t*(pt_bot[1] - pt_top[1]))
                    plt.plot(cx, cy, color='#1e3a8a', lw=1.2, alpha=0.6)
                for i in range(1, 6):
                    f = i / 6.0
                    pt_left = (B2in[0] + f*(B2[0]-B2in[0]), B2in[1] + f*(B2[1]-B2in[1]))
                    pt_right = (B1in[0] + f*(B1[0]-B1in[0]), B1in[1] + f*(B1[1]-B1in[1]))
                    cx, cy = [], []
                    for j in range(11):
                        t = j / 10.0
                        bulge = 0.12 * aw * math.sin(t * math.pi)
                        cx.append(pt_left[0] + t*(pt_right[0] - pt_left[0]))
                        cy.append(pt_left[1] + t*(pt_right[1] - pt_left[1]) + bulge)
                    plt.plot(cx, cy, color='#991b1b', lw=1.2, alpha=0.6)
            else:
                for i in range(1, 6):
                    f = i / 6.0
                    pt_top = (A1in[0] + f*(A1[0]-A1in[0]), A1in[1] + f*(A1[1]-A1in[1]))
                    pt_bot = (A2in[0] + f*(A2[0]-A2in[0]), A2in[1] + f*(A2[1]-A2in[1]))
                    plt.plot([pt_top[0], pt_bot[0]], [pt_top[1], pt_bot[1]], color='#1e3a8a', lw=1.2, alpha=0.6)
                for i in range(1, 6):
                    f = i / 6.0
                    pt_left = (B2in[0] + f*(B2[0]-B2in[0]), B2in[1] + f*(B2[1]-B2in[1]))
                    pt_right = (B1in[0] + f*(B1[0]-B1in[0]), B1in[1] + f*(B1[1]-B1in[1]))
                    plt.plot([pt_left[0], pt_right[0]], [pt_left[1], pt_right[1]], color='#991b1b', lw=1.2, alpha=0.6)

            plt.plot([0, L1], [0, L2], color='#475569', linestyle='--', lw=1.5)
            plt.plot([0, L1], [0, -L2], color='#475569', linestyle='--', lw=1.5)
            plt.plot([0, -L1], [0, L2], color='#475569', linestyle='--', lw=1.5)
            plt.plot([-back_x1*0.2, back_x1*1.2], [0, 0], 'k-.', lw=1)
            plt.plot([0, 0], [-back_y2*0.2, back_y2*1.2], 'k-.', lw=1)
            plt.plot(0, 0, 'ko', markersize=6)
            plt.text(back_x1/2, -back_y2*0.15, f'Re = {aw:.2f} mm', ha='center', fontweight='bold', color='#1e293b')
        else:
            c1 = plt.Circle((0, 0), d1/2, color='#3b82f6', fill=True, alpha=0.2, linewidth=2)
            ax.add_patch(c1)
            c1_edge = plt.Circle((0, 0), d1/2, color='#1e3a8a', fill=False, linewidth=2, linestyle='--')
            ax.add_patch(c1_edge)
            c2 = plt.Circle((aw, 0), d2/2, color='#ef4444', fill=True, alpha=0.2, linewidth=2)
            ax.add_patch(c2)
            c2_edge = plt.Circle((aw, 0), d2/2, color='#991b1b', fill=False, linewidth=2, linestyle='--')
            ax.add_patch(c2_edge)
            plt.plot(0, 0, 'ko', markersize=8)
            plt.plot(aw, 0, 'ko', markersize=8)
            plt.plot([0, aw], [0, 0], color='#475569', linestyle='-.')
            plt.text(aw/2, 10, f'aw = {aw:.2f} mm', ha='center', fontweight='bold', color='#1e293b')
            if loai_br == 'nghieng':
                for i in range(-int(d1/4), int(d1/4), 10):
                    plt.plot([i, i+8], [d1/2-10, d1/2], color='#1e3a8a', linewidth=1)
                for i in range(int(aw-d2/4), int(aw+d2/4), 20):
                    plt.plot([i, i-12], [d2/2-15, d2/2], color='#991b1b', linewidth=1)
                plt.text(aw/2, -aw/4, "(Mô phỏng Bánh Răng Trụ Nghiêng)", ha='center', color='#64748b', fontstyle='italic')
            else:
                plt.text(aw/2, -aw/4, "(Mô phỏng Bánh Răng Trụ Thẳng)", ha='center', color='#64748b', fontstyle='italic')
                
        plt.axis('equal')
        plt.axis('off')
        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        encoded_img = base64.b64encode(img.read()).decode('utf-8')
        plt.close('all')
        return encoded_img
    except Exception: return ""

def draw_planetary_schematic(d1, d2, aw, nw, za, zc, zb):
    try:
        plt.close('all')
        plt.figure(figsize=(8, 8))
        ax = plt.gca()
        da = d1; dc = d2; db = da + 2*dc 
        r_a = da / 2; r_c = dc / 2; r_b = db / 2
        ring_outer = plt.Circle((0, 0), r_b + 10, color='#94a3b8', fill=True, alpha=0.3)
        ring_inner = plt.Circle((0, 0), r_b, color='white', fill=True)
        ring_edge = plt.Circle((0, 0), r_b, color='#334155', fill=False, linewidth=2, linestyle='--')
        ax.add_patch(ring_outer); ax.add_patch(ring_inner); ax.add_patch(ring_edge)
        sun = plt.Circle((0, 0), r_a, color='#ef4444', fill=True, alpha=0.4, linewidth=2)
        sun_edge = plt.Circle((0, 0), r_a, color='#991b1b', fill=False, linewidth=2)
        ax.add_patch(sun); ax.add_patch(sun_edge)
        plt.plot(0, 0, 'k+', markersize=15)
        angles = [i * (360 / nw) for i in range(nw)]
        for angle in angles:
            rad = math.radians(angle)
            cx = aw * math.cos(rad)
            cy = aw * math.sin(rad)
            planet = plt.Circle((cx, cy), r_c, color='#3b82f6', fill=True, alpha=0.4, linewidth=2)
            planet_edge = plt.Circle((cx, cy), r_c, color='#1e3a8a', fill=False, linewidth=2)
            ax.add_patch(planet); ax.add_patch(planet_edge)
            plt.plot(cx, cy, 'ko', markersize=5)
            plt.plot([0, cx], [0, cy], color='#f59e0b', linewidth=3, linestyle='-', alpha=0.7)
        plt.text(0, r_b + 20, f"SƠ ĐỒ HÀNH TINH A (c = {nw})", ha='center', fontweight='bold', color='#1e293b', fontsize=14)
        plt.text(0, -r_b - 25, f"Z1={za}, Z2={zc}, Z3={zb} | aw={aw:.1f}mm", ha='center', color='#64748b', fontstyle='italic', fontsize=12)
        plt.axis('equal'); plt.axis('off'); plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', bbox_inches='tight')
        img.seek(0)
        encoded_img = base64.b64encode(img.read()).decode('utf-8')
        plt.close('all')
        return encoded_img
    except Exception: return ""

HTML_PAGE = r"""
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hệ Thống Thiết Kế Bánh Răng Tổng Hợp</title>
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f4f8; margin: 0; padding: 20px; color: #1e293b; }
    .container { max-width: 1250px; margin: auto; background: #ffffff; padding: 30px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #0f172a; border-bottom: 3px solid #3b82f6; padding-bottom: 15px; text-transform: uppercase; margin-top: 0;}
    h2 { color: #b91c1c; border-bottom: 2px dashed #f87171; padding-bottom: 10px; text-transform: uppercase; margin-top: 20px;}
    
    /* Chung */
    .grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
    .grid-5 { display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px; }
    .grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; margin-bottom: 20px; }
    .grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }
    label { font-weight: 600; font-size: 14px; color: #475569; display: block; margin-bottom: 5px; margin-top: 10px;}
    input, select { width: 100%; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; font-size: 15px; background-color: #f8fafc; }
    button { width: 100%; color: white; padding: 15px; border: none; border-radius: 6px; font-size: 18px; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px; text-transform: uppercase;}
    .result-box { margin-top: 20px; padding: 25px; border: 2px solid #10b981; border-radius: 8px; background-color: #f8fafc; }
    table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; background: white;}
    th, td { padding: 10px; border: 1px solid #e2e8f0; text-align: left; }
    tr:nth-child(even) { background-color: #f8fafc; }
    .highlight { color: #dc2626; font-weight: bold; }
    .success { color: #16a34a; font-weight: bold; }
    input[readonly] { background-color: #e2e8f0; color: #b91c1c; font-weight: bold; }

    /* Theme Hành Tinh (tt_ranght4) */
    .ht-theme h3 { background-color: #2563eb; color: white; padding: 12px 15px; border-radius: 6px; font-size: 16px; margin-top: 30px; margin-bottom: 10px;}
    .ht-theme th { background-color: #eff6ff; color: #1e40af; width: 35%; }
    .ht-theme .material-panel { background: #f8fafc; border: 1px solid #cbd5e1; padding: 20px; border-radius: 8px;}
    .ht-theme button { background-color: #059669; }
    .ht-theme button:hover { background-color: #047857; }
    .error-box { background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-top: 15px; font-size: 14px; color: #b91c1c; font-weight: bold;}
    
    /* Theme Chung (tt_rang7.3) */
    .gen-theme h3 { background-color: #3b82f6; color: white; padding: 12px 15px; border-radius: 6px; font-size: 18px; margin-top: 30px; margin-bottom: 10px;}
    .gen-theme th { background-color: #eff6ff; color: #1e3a8a; font-weight: 600; text-align: center;}
    .gen-theme td { text-align: center; }
    .gen-theme .material-panel { background: #f8fafc; border: 1px solid #cbd5e1; padding: 15px; border-radius: 8px; margin-bottom: 15px;}
    .gen-theme button { background-color: #2563eb; }
    .gen-theme button:hover { background-color: #1d4ed8; }
    .gen-theme .step-title { background-color: #2563eb !important; color: white !important; font-weight: bold; text-align: center; font-size: 16px;}

</style>
<script>
    // Dữ liệu JS
    const genMatDB = {{ gen_mat_db_json | safe }};
    const genSHlimDB = {{ gen_shlim_db_json | safe }};
    const genSFlimDB = {{ gen_sflim_db_json | safe }};
    
    const htMatDB = {{ ht_mat_db_json | safe }};
    const htStressDB = {{ ht_stress_db_json | safe }};

    function updateGenMaterial(prefix) {
        const matKey = document.getElementById(prefix + '_mat').value;
        const matData = genMatDB[matKey];
        
        const hardLabel = document.getElementById(prefix + '_hard_label');
        const hardInput = document.getElementById(prefix + '_hard_val');
        hardLabel.innerHTML = `Độ cứng ${matData.hard_type} (Gợi ý: ${matData.hard_min} - ${matData.hard_max}):`;
        hardInput.min = matData.hard_min;
        hardInput.max = matData.hard_max;
        if (!hardInput.value) hardInput.value = Math.floor((matData.hard_min + matData.hard_max) / 2);

        const optSelect = document.getElementById(prefix + '_opt');
        optSelect.innerHTML = '';
        matData.options.forEach((opt, index) => {
            let option = document.createElement('option');
            option.value = index;
            option.text = `${opt.label} (σb=${opt.sb}, σch=${opt.sch})`;
            optSelect.add(option);
        });

        const hForm = document.getElementById(prefix + '_sH_form');
        const fForm = document.getElementById(prefix + '_sF_form');
        hForm.innerHTML = ''; fForm.innerHTML = '';
        
        genSHlimDB.forEach(f => { if (f.type === matData.type) { let opt = document.createElement('option'); opt.value = f.id; opt.text = f.name; hForm.add(opt); } });
        genSFlimDB.forEach(f => { if (f.type === matData.type) { let opt = document.createElement('option'); opt.value = f.id; opt.text = f.name; fForm.add(opt); } });
        updateGenPsiBa();
    }

    function updateGenPsiBa() {
        const hb1 = parseFloat(document.getElementById('b1_hard_val').value) || 0;
        const hb2 = parseFloat(document.getElementById('b2_hard_val').value) || 0;
        const mat1 = genMatDB[document.getElementById('b1_mat').value];
        const mat2 = genMatDB[document.getElementById('b2_mat').value];
        const eff_hb1 = mat1.hard_type === 'HRC' ? hb1 * 10 : hb1;
        const eff_hb2 = mat2.hard_type === 'HRC' ? hb2 * 10 : hb2;

        const isHard = (eff_hb1 > 350 && eff_hb2 > 350); 
        const botri = document.getElementById('bo_tri').value;
        const loaiBr = document.getElementById('loai_br').value;
        let min=0.3, max=0.5, def=0.4;
        
        if (loaiBr === 'con_thang' || loaiBr === 'con_cong') {
            document.getElementById('psi_ba_hint').innerText = `Răng Côn (Kbe thường lấy 0.25 - 0.3)`;
            document.getElementById('psi_ba').value = 0.25;
            return;
        }

        if (loaiBr === 'hanh_tinh') {
            return;
        }

        if (botri === 'doixung') { min = isHard ? 0.25 : 0.3; max = isHard ? 0.3 : 0.5; def = isHard ? 0.28 : 0.4; }
        else if (botri === 'khong_doixung') { min = isHard ? 0.2 : 0.25; max = isHard ? 0.25 : 0.4; def = isHard ? 0.22 : 0.3; }
        else if (botri === 'chia') { min = isHard ? 0.15 : 0.2; max = isHard ? 0.2 : 0.25; def = isHard ? 0.18 : 0.22; }

        const psiInput = document.getElementById('psi_ba');
        document.getElementById('psi_ba_hint').innerText = `Gợi ý bảng tra: ${min} - ${max}`;
        psiInput.min = min; psiInput.max = max;
        if (!psiInput.getAttribute('data-touched')) psiInput.value = def;
    }

    function toggleKMode() {
        const mode = document.getElementById('k_mode').value;
        const els = document.querySelectorAll('.manual-k');
        els.forEach(el => el.style.display = mode === 'manual' ? 'block' : 'none');
    }

    function autoCalcKinematics() {
        const n1 = parseFloat(document.getElementById('ht_n1').value);
        const n0 = parseFloat(document.getElementById('ht_n0').value);
        if (n1 && n0 && n0 !== 0) {
            const u10 = n1 / n0;
            document.getElementById('ht_u10_display').value = u10.toFixed(3);
        }
    }

    function updateHtMaterial(prefix) {
        const matKey = document.getElementById('ht_' + prefix + '_mat').value;
        const matData = htMatDB[matKey];
        
        const hardLabel = document.getElementById('ht_' + prefix + '_hard_label');
        const hardInput = document.getElementById('ht_' + prefix + '_hard_val');
        hardLabel.innerHTML = `Độ cứng ${matData.type} (${matData.h_min} - ${matData.h_max}):`;
        hardInput.min = matData.h_min; hardInput.max = matData.h_max;
        if (!hardInput.value) hardInput.value = Math.floor((matData.h_min + matData.h_max) / 2);

        const optSelect = document.getElementById('ht_' + prefix + '_opt');
        if(optSelect) {
            optSelect.innerHTML = '';
            matData.options.forEach((opt, idx) => {
                let option = document.createElement('option');
                option.value = idx;
                option.text = `${opt.label} (σb=${opt.sb}, σch=${opt.sch})`;
                optSelect.add(option);
            });
        }

        const stressSelect = document.getElementById('ht_' + prefix + '_stress');
        if(stressSelect) {
            stressSelect.innerHTML = '';
            htStressDB.forEach(f => {
                if (f.type === matData.type) {
                    let opt = document.createElement('option');
                    opt.value = f.id; opt.text = f.name;
                    stressSelect.add(opt);
                }
            });
        }
    }

    function toggleGearType() {
        const loaiBr = document.getElementById('loai_br').value;
        const generalUi = document.getElementById('general_ui');
        const htUi = document.getElementById('ht_ui');
        
        if (loaiBr === 'hanh_tinh') {
            generalUi.style.display = 'none';
            htUi.style.display = 'block';
        } else {
            generalUi.style.display = 'block';
            htUi.style.display = 'none';
            
            const isNghieng = loaiBr === 'nghieng';
            const isConCong = loaiBr === 'con_cong';
            const betaInput = document.querySelector('input[name="beta_sb"]');
            
            if (isNghieng) {
                betaInput.readOnly = false;
                betaInput.min = 8; betaInput.max = 20;
                if (betaInput.value == 0 || betaInput.value == 35) betaInput.value = 10;
            } else if (isConCong) {
                betaInput.readOnly = false;
                betaInput.min = 20; betaInput.max = 40;
                if (betaInput.value == 0 || betaInput.value == 10) betaInput.value = 35;
            } else {
                betaInput.readOnly = true;
                betaInput.min = 0; betaInput.max = 0; betaInput.value = 0;
            }
            updateGenPsiBa();
        }
    }

    window.onload = function() {
        document.getElementById('b1_hard_val').addEventListener('input', updateGenPsiBa);
        document.getElementById('b2_hard_val').addEventListener('input', updateGenPsiBa);
        document.getElementById('psi_ba').addEventListener('input', function() { this.setAttribute('data-touched', 'true'); });
        updateGenMaterial('b1'); 
        updateGenMaterial('b2');

        updateHtMaterial('b1'); 
        updateHtMaterial('b3');
        document.getElementById('ht_n1').addEventListener('input', autoCalcKinematics);
        document.getElementById('ht_n0').addEventListener('input', autoCalcKinematics);
        autoCalcKinematics();

        {% if request.method == 'POST' %}
            if(document.getElementById('b1_opt')) document.getElementById('b1_opt').value = "{{ request.form.get('b1_opt', '0') }}";
            if(document.getElementById('b1_sH_form')) document.getElementById('b1_sH_form').value = "{{ request.form.get('b1_sH_form', '') }}";
            if(document.getElementById('b1_sF_form')) document.getElementById('b1_sF_form').value = "{{ request.form.get('b1_sF_form', '') }}";
            if(document.getElementById('b2_opt')) document.getElementById('b2_opt').value = "{{ request.form.get('b2_opt', '0') }}";
            if(document.getElementById('b2_sH_form')) document.getElementById('b2_sH_form').value = "{{ request.form.get('b2_sH_form', '') }}";
            if(document.getElementById('b2_sF_form')) document.getElementById('b2_sF_form').value = "{{ request.form.get('b2_sF_form', '') }}";
            document.getElementById('psi_ba').setAttribute('data-touched', 'true');
            
            if (document.getElementById('ht_b1_stress')) document.getElementById('ht_b1_stress').value = "{{ request.form.get('ht_b1_stress', '') }}";
            if (document.getElementById('ht_b3_stress')) document.getElementById('ht_b3_stress').value = "{{ request.form.get('ht_b3_stress', '') }}";
            if (document.getElementById('ht_b1_opt')) document.getElementById('ht_b1_opt').value = "{{ request.form.get('ht_b1_opt', '0') }}";
            if (document.getElementById('ht_b3_opt')) document.getElementById('ht_b3_opt').value = "{{ request.form.get('ht_b3_opt', '0') }}";
        {% endif %}

        toggleKMode();
        toggleGearType();
    };
</script>
</head>
<body>
<div class="container">
    <h1>Phần Mềm Thiết Kế Bánh Răng Tổng Hợp</h1>

    <div style="background: #eef2ff; padding: 20px; border-radius: 8px; border: 2px solid #6366f1; margin-bottom: 20px;">
        <label style="font-size: 18px; color: #3730a3; margin-top:0;">CHỌN CHẾ ĐỘ THIẾT KẾ / LOẠI BÁNH RĂNG:</label>
        <select name="loai_br" id="loai_br" form="main_form" onchange="toggleGearType()" style="font-size: 16px; padding: 12px; font-weight: bold; color: #1e3a8a;">
            <option value="nghieng" {% if request.form.get('loai_br') == 'nghieng' %}selected{% endif %}>⚙️ Răng Trụ Nghiêng</option>
            <option value="thang" {% if request.form.get('loai_br') == 'thang' %}selected{% endif %}>⚙️ Răng Trụ Thẳng</option>
            <option value="con_thang" {% if request.form.get('loai_br') == 'con_thang' %}selected{% endif %}>📐 Răng Côn Thẳng</option>
            <option value="con_cong" {% if request.form.get('loai_br') == 'con_cong' %}selected{% endif %}>📐 Răng Côn Cung Tròn</option>
            <option value="hanh_tinh" {% if request.form.get('loai_br') == 'hanh_tinh' %}selected{% endif %} style="color:#b91c1c;">🚀 Hộp Hành Tinh </option>
        </select>
    </div>

    <form method="POST" id="main_form">
        
        <div id="general_ui" class="gen-theme">
            <h3>BƯỚC 0: CÁC THÔNG SỐ ĐẦU VÀO</h3>
            <div class="grid-4">
                <div><label>Công suất P1 (kW):</label><input type="number" step="any" name="P1" value="{{ request.form.get('P1', '15.7') }}"></div>
                <div><label>Vòng quay n1 (vg/ph):</label><input type="number" step="any" name="n1" value="{{ request.form.get('n1', '187.5') }}"></div>
                <div><label>Tỉ số truyền u:</label><input type="number" step="any" name="ud" value="{{ request.form.get('ud', '5') }}"></div>
                <div><label>T.gian phục vụ Lh (h):</label><input type="number" step="any" name="Lh" value="{{ request.form.get('Lh', '5000') }}"></div>
            </div>
            <div class="grid-3">
                <div><label>Góc nghiêng sơ bộ β (độ):</label>
                    <input type="number" step="any" name="beta_sb" value="{{ request.form.get('beta_sb', '35') }}">
                </div>
                <div><label>Chiều tải trọng (KFC):</label>
                    <select name="kfc" id="kfc">
                        <option value="1.0" {% if request.form.get('kfc', '1.0') == '1.0' %}selected{% endif %}>Quay 1 chiều (KFC = 1.0)</option>
                        <option value="0.75" {% if request.form.get('kfc') == '0.75' %}selected{% endif %}>Quay 2 chiều (KFC = 0.75)</option>
                    </select>
                </div>
                <div><label>Hệ số quá tải Kqt:</label><input type="number" step="any" name="Kqt" value="{{ request.form.get('Kqt', '2.0') }}"></div>
            </div>

            <div style="background:#e0f2fe; padding:15px; border:1px solid #38bdf8; border-radius:8px; margin-bottom: 20px; margin-top: 10px;">
                <h4 style="margin-top:0; color:#0369a1; border-bottom: 1px solid #7dd3fc; padding-bottom: 5px;">QUYỀN ĐIỀU KHIỂN HỆ SỐ & TRA BẢNG</h4>
                <div class="grid-5" style="margin-bottom:0;">
                    <div><label>Chế độ KHβ, KFβ:</label>
                        <select name="k_mode" id="k_mode" onchange="toggleKMode()">
                            <option value="manual" {% if request.form.get('k_mode') == 'manual' %}selected{% endif %}>Nhập tay </option>
                            <option value="auto" {% if request.form.get('k_mode', 'auto') == 'auto' %}selected{% endif %}>Tự động tra Bảng 6.7</option>
                        </select>
                    </div>
                    <div class="manual-k"><label>Nhập KHβ:</label><input type="number" step="any" name="KHb_user" value="{{ request.form.get('KHb_user', '1.0') }}"></div>
                    <div class="manual-k"><label>Nhập KFβ:</label><input type="number" step="any" name="KFb_user" value="{{ request.form.get('KFb_user', '1.14') }}"></div>
                    <div><label>Hệ số nhám ZR:</label><input type="number" step="any" name="ZR" value="{{ request.form.get('ZR', '0.95') }}"></div>
                    <div><label>Hệ số Mô-đun (0.01-0.02):</label><input type="number" step="0.001" name="m_coef" value="{{ request.form.get('m_coef', '0.015') }}"></div>
                </div>
            </div>

            <h3>BƯỚC 1 & 2: VẬT LIỆU, ỨNG SUẤT VÀ SƠ ĐỒ BỐ TRÍ</h3>
            <div class="grid-2">
                <div class="material-panel">
                    <h4 style="margin-top:0; color:#1d4ed8;">VẬT LIỆU BÁNH 1 (CHỦ ĐỘNG)</h4>
                    <label>Mác thép:</label>
                    <select name="b1_mat" id="b1_mat" onchange="updateGenMaterial('b1')">
                        {% for key, val in gen_mat_db.items() %}
                        <option value="{{ key }}" {% if request.form.get('b1_mat', '40XH_TBM') == key %}selected{% endif %}>{{ val.name }}</option>
                        {% endfor %}
                    </select>
                    <label id="b1_hard_label">Nhập độ cứng:</label>
                    <input type="number" step="1" name="b1_hard_val" id="b1_hard_val" value="{{ request.form.get('b1_hard_val', '52') }}">
                    <label>Lựa chọn phôi (σb & σch):</label><select name="b1_opt" id="b1_opt"></select>
                    <label>Công thức σHlim:</label><select name="b1_sH_form" id="b1_sH_form"></select>
                    <label>Công thức σFlim:</label><select name="b1_sF_form" id="b1_sF_form"></select>
                </div>
                <div class="material-panel">
                    <h4 style="margin-top:0; color:#1d4ed8;">VẬT LIỆU BÁNH 2 (BỊ DẪN)</h4>
                    <label>Mác thép:</label>
                    <select name="b2_mat" id="b2_mat" onchange="updateGenMaterial('b2')">
                        {% for key, val in gen_mat_db.items() %}
                        <option value="{{ key }}" {% if request.form.get('b2_mat', '40X_TC') == key %}selected{% endif %}>{{ val.name }}</option>
                        {% endfor %}
                    </select>
                    <label id="b2_hard_label">Nhập độ cứng:</label>
                    <input type="number" step="1" name="b2_hard_val" id="b2_hard_val" value="{{ request.form.get('b2_hard_val', '230') }}">
                    <label>Lựa chọn phôi (σb & σch):</label><select name="b2_opt" id="b2_opt"></select>
                    <label>Công thức σHlim:</label><select name="b2_sH_form" id="b2_sH_form"></select>
                    <label>Công thức σFlim:</label><select name="b2_sF_form" id="b2_sF_form"></select>
                </div>
            </div>
            
            <div style="background:#fffbeb; padding:15px; border:1px solid #f59e0b; border-radius:8px;">
                <div class="grid-2" style="margin-bottom:0;">
                    <div>
                        <label>Sơ đồ bố trí ổ (Trục):</label>
                        <select name="bo_tri" id="bo_tri" onchange="updateGenPsiBa()">
                            <option value="khong_doixung" {% if request.form.get('bo_tri', 'khong_doixung') == 'khong_doixung' %}selected{% endif %}>Bố trí Không đối xứng</option>
                            <option value="doixung" {% if request.form.get('bo_tri') == 'doixung' %}selected{% endif %}>Bố trí Đối xứng</option>
                            <option value="chia" {% if request.form.get('bo_tri') == 'chia' %}selected{% endif %}>Bố trí Chia / Công sôn (Bánh nón)</option>
                        </select>
                    </div>
                    <div>
                        <label>Hệ số chiều rộng vành răng ($\psi_{ba}$ hoặc Kbe): <span id="psi_ba_hint" style="color:#d97706; font-size:12px;"></span></label>
                        <input type="number" step="0.001" name="psi_ba" id="psi_ba" value="{{ request.form.get('psi_ba', '0.7') }}">
                    </div>
                </div>
            </div>
            <button type="submit">Thực Hiện Thiết Kế Bánh Răng</button>
        </div>

        <div id="ht_ui" class="ht-theme" style="display: none;">
            <h3>1. THÔNG SỐ ĐỘNG HỌC & YÊU CẦU</h3>
            <div class="grid-4">
                <div><label>Công suất trục ra Po (kW):</label><input type="number" step="any" name="ht_Po" value="{{ request.form.get('ht_Po', '15.7') }}"></div>
                <div><label>Số vòng quay n1 (vg/ph):</label><input type="number" step="any" id="ht_n1" name="ht_n1" value="{{ request.form.get('ht_n1', '187.5') }}"></div>
                <div><label>Số vòng quay no (vg/ph):</label><input type="number" step="any" id="ht_n0" name="ht_n0" value="{{ request.form.get('ht_n0', '37.5') }}"></div>
                <div><label>Tỉ số truyền u10 (Auto):</label><input type="text" id="ht_u10_display" readonly style="background:#e2e8f0;"></div>
                
                <div><label>Thông số e :</label><input type="number" step="any" name="ht_e_val" value="{{ request.form.get('ht_e_val', '4.0') }}"></div>
                <div><label>Số vệ tinh c:</label><input type="number" name="ht_c" value="{{ request.form.get('ht_c', '3') }}"></div>
                <div><label>Thời hạn sử dụng Lh (h):</label><input type="number" name="ht_Lh" value="{{ request.form.get('ht_Lh', '5000') }}"></div>
                <div><label>Hệ số quá tải Kqt:</label><input type="number" step="any" name="ht_Kqt" value="{{ request.form.get('ht_Kqt', '2.0') }}"></div>
            </div>

            <h3>2. CÁC HỆ SỐ TRA BẢNG CẦN THIẾT (TỰ DO NHẬP)</h3>
            <div class="grid-4">
                <div><label>Hệ số dạng răng Kd:</label><input type="number" step="any" name="ht_Kd" value="{{ request.form.get('ht_Kd', '77') }}"></div>
                <div><label>Hệ số phân tải vệ tinh Kc (Răng):</label><input type="number" step="any" name="ht_Kc_rang" value="{{ request.form.get('ht_Kc_rang', '1.2') }}"></div>
                <div><label>Hệ số tải trọng sơ bộ KHΣ:</label><input type="number" step="any" name="ht_KH_Sigma" value="{{ request.form.get('ht_KH_Sigma', '1.3') }}"></div>
                <div><label>Hệ số chiều rộng ψbd:</label><input type="number" step="any" name="ht_psiba" value="{{ request.form.get('ht_psiba', '0.7') }}"></div>
                
                <div><label>Hệ số cơ tính ZM (MPa^1/3):</label><input type="number" step="any" name="ht_ZM" value="{{ request.form.get('ht_ZM', '274') }}"></div>
                <div><label>Hệ số dạng răng mặt trời YF1:</label><input type="number" step="any" name="ht_YF1" value="{{ request.form.get('ht_YF1', '4.13') }}"></div>
                <div><label>Hệ số dạng răng vệ tinh YF2:</label><input type="number" step="any" name="ht_YF2" value="{{ request.form.get('ht_YF2', '3.8') }}"></div>
                <div><label>Hệ số dạng răng bao YF3:</label><input type="number" step="any" name="ht_YF3" value="{{ request.form.get('ht_YF3', '3.35') }}"></div>
            </div>

            <h3>3. CHIỀU TẢI TRỌNG & THÔNG SỐ Ổ LĂN</h3>
            <div class="grid-3">
                <div><label>KFC Bánh 1 (Mặt trời):</label>
                    <select name="ht_kfc_1"><option value="1.0" {% if request.form.get('ht_kfc_1', '1.0') == '1.0' %}selected{% endif %}>1 Phía (Quay 1 chiều) - 1.0</option><option value="0.75" {% if request.form.get('ht_kfc_1') == '0.75' %}selected{% endif %}>2 Phía (Đảo chiều) - 0.75</option></select>
                </div>
                <div><label>KFC Bánh 2 (Vệ tinh):</label>
                    <select name="ht_kfc_2"><option value="0.75" {% if request.form.get('ht_kfc_2', '0.75') == '0.75' %}selected{% endif %}>2 Phía (Đảo chiều) - 0.75</option><option value="1.0" {% if request.form.get('ht_kfc_2') == '1.0' %}selected{% endif %}>1 Phía (Quay 1 chiều) - 1.0</option></select>
                </div>
                <div><label>KFC Bánh 3 (Vành bao):</label>
                    <select name="ht_kfc_3"><option value="1.0" {% if request.form.get('ht_kfc_3', '1.0') == '1.0' %}selected{% endif %}>1 Phía (Quay 1 chiều) - 1.0</option><option value="0.75" {% if request.form.get('ht_kfc_3') == '0.75' %}selected{% endif %}>2 Phía (Đảo chiều) - 0.75</option></select>
                </div>
            </div>
            <div class="grid-4">
                <div><label>Tải động C của ổ (kN):</label><input type="number" step="any" name="ht_C_kN" value="{{ request.form.get('ht_C_kN', '64.9') }}"></div>
                <div><label>Hệ số phân tải Kc (Ổ lăn):</label><input type="number" step="any" name="ht_Kc_o" value="{{ request.form.get('ht_Kc_o', '1.1') }}"></div>
                <div><label>Hệ số vòng quay V:</label><input type="number" step="any" name="ht_V_olan" value="{{ request.form.get('ht_V_olan', '1.2') }}"></div>
                <div><label>Hệ số an toàn s:</label><input type="number" step="any" name="ht_s_olan" value="{{ request.form.get('ht_s_olan', '1.3') }}"></div>
            </div>

            <h3>4. VẬT LIỆU BÁNH RĂNG (Tra cứu Bảng 6.1 & 6.2)</h3>
            <div class="grid-2">
                <div class="material-panel">
                    <h4 style="margin-top:0; color:#b91c1c;">VẬT LIỆU BÁNH 1 & 2 (Mặt trời & Vệ tinh)</h4>
                    <label>Mác thép (Bảng 6.1):</label>
                    <select name="ht_b1_mat" id="ht_b1_mat" onchange="updateHtMaterial('b1')">
                        {% for key, val in ht_mat_db.items() %}<option value="{{ key }}" {% if request.form.get('ht_b1_mat', '40XH_T') == key %}selected{% endif %}>{{ val.name }}</option>{% endfor %}
                    </select>
                    <label id="ht_b1_hard_label">Độ cứng HRC:</label><input type="number" step="1" name="ht_b1_hard_val" id="ht_b1_hard_val" value="{{ request.form.get('ht_b1_hard_val', '52') }}">
                    <label>Kích thước Phôi & Cơ tính:</label><select name="ht_b1_opt" id="ht_b1_opt"></select>
                    <label>Nhiệt luyện ứng suất (Bảng 6.2):</label><select name="ht_b1_stress" id="ht_b1_stress"></select>
                </div>
                
                <div class="material-panel">
                    <h4 style="margin-top:0; color:#b91c1c;">VẬT LIỆU BÁNH 3 (Vành răng bao)</h4>
                    <label>Mác thép (Bảng 6.1):</label>
                    <select name="ht_b3_mat" id="ht_b3_mat" onchange="updateHtMaterial('b3')">
                        {% for key, val in ht_mat_db.items() %}<option value="{{ key }}" {% if request.form.get('ht_b3_mat', '40X') == key %}selected{% endif %}>{{ val.name }}</option>{% endfor %}
                    </select>
                    <label id="ht_b3_hard_label">Độ cứng HB:</label><input type="number" step="1" name="ht_b3_hard_val" id="ht_b3_hard_val" value="{{ request.form.get('ht_b3_hard_val', '230') }}">
                    <label>Kích thước Phôi & Cơ tính:</label><select name="ht_b3_opt" id="ht_b3_opt"></select>
                    <label>Nhiệt luyện ứng suất (Bảng 6.2):</label><select name="ht_b3_stress" id="ht_b3_stress"></select>
                </div>
            </div>
            <button type="submit">Thực Hiện Tính Toán Hành Tinh</button>
        </div>
    </form>

    {% if result_html %}
    <div class="result-box table-left" style="display:block;">
        {{ result_html | safe }}
    </div>
    {% endif %}
</div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    result_html = ""
    if request.method == 'POST':
        loai_br = request.form.get('loai_br')
        
        # =====================================================================
        # NHÁNH 1: XỬ LÝ CHO BÁNH RĂNG TRỤ VÀ NÓN (TỪ TT_RANG7.3.PY)
        # =====================================================================
        if loai_br != 'hanh_tinh':
            try:
                P1 = float(request.form.get('P1', 15.7))
                n1 = float(request.form.get('n1', 187.5))
                u = float(request.form.get('ud', 5))
                Lh = float(request.form.get('Lh', 5000))
                Kqt = float(request.form.get('Kqt', 1.8))
                KFC = float(request.form.get('kfc', 1.0))
                psiba = float(request.form.get('psi_ba', 0.3))
                bo_tri = request.form.get('bo_tri')
                
                beta_sb_deg = 0.0 if loai_br in ['thang', 'con_thang'] else float(request.form.get('beta_sb', 10))
                ZR = float(request.form.get('ZR', 0.95))
                k_mode = request.form.get('k_mode', 'auto')
                KHb_user = float(request.form.get('KHb_user', 1.13))
                KFb_user = float(request.form.get('KFb_user', 1.28))
                m_coef = float(request.form.get('m_coef', 0.015))
                
                b1_mat_key = request.form.get('b1_mat')
                b1_hard_val = float(request.form.get('b1_hard_val', 52))
                b1_opt_idx = int(request.form.get('b1_opt', 0))
                b1_sh_f = request.form.get('b1_sH_form')
                b1_sf_f = request.form.get('b1_sF_form')
                mat1 = GENERAL_MATERIAL_DB[b1_mat_key]
                mat1_props = mat1['options'][b1_opt_idx]
                HB1 = b1_hard_val if mat1['hard_type'] == 'HB' else b1_hard_val * 10 
                
                b2_mat_key = request.form.get('b2_mat')
                b2_hard_val = float(request.form.get('b2_hard_val', 230))
                b2_opt_idx = int(request.form.get('b2_opt', 0))
                b2_sh_f = request.form.get('b2_sH_form')
                b2_sf_f = request.form.get('b2_sF_form')
                mat2 = GENERAL_MATERIAL_DB[b2_mat_key]
                mat2_props = mat2['options'][b2_opt_idx]
                HB2 = b2_hard_val if mat2['hard_type'] == 'HB' else b2_hard_val * 10

                sH_max_cp = min(2.8 * mat1_props['sch'], 2.8 * mat2_props['sch'])
                sF1_max_cp = 0.8 * mat1_props['sch']
                sF2_max_cp = 0.8 * mat2_props['sch']

                if mat1['type'] == 'cung' and mat2['type'] == 'cung':
                    mat_check, mat_color = "ĐẠT (Hai bánh tôi cứng)", "success"
                else:
                    mat_check, mat_color = ("ĐẠT", "success") if HB1 >= HB2 + 10 else ("CẢNH BÁO (Nên HB1 > HB2 + 10-15)", "highlight")

                sHlim1_0 = calculate_shlim(b1_sh_f, b1_hard_val)
                sHlim2_0 = calculate_shlim(b2_sh_f, b2_hard_val)
                sFlim1_0 = calculate_sflim(b1_sf_f, b1_hard_val)
                sFlim2_0 = calculate_sflim(b2_sf_f, b2_hard_val)

                NHO1 = 30 * (HB1 ** 2.4); NHO2 = 30 * (HB2 ** 2.4)
                n2 = n1 / u
                NHE2 = 60 * 1 * n2 * Lh; NHE1 = u * NHE2
                KHL1 = 1.0 if NHE1 >= NHO1 else (NHO1/NHE1)**(1/6)
                KHL2 = 1.0 if NHE2 >= NHO2 else (NHO2/NHE2)**(1/6)
                SH1 = 1.1 if mat1['type'] == 'mem' else 1.2
                SH2 = 1.1 if mat2['type'] == 'mem' else 1.2
                
                sH_cp1_base = (sHlim1_0 / SH1) * KHL1
                sH_cp2_base = (sHlim2_0 / SH2) * KHL2
                
                sF_cp1 = (sFlim1_0 / 1.75) * KFC
                sF_cp2 = (sFlim2_0 / 1.75) * KFC

                T1 = 9.55 * (10**6) * P1 / n1

                if loai_br in ['thang', 'nghieng']:
                    sH_cp_base = min(sH_cp1_base, sH_cp2_base) if loai_br == 'thang' else min(1.25 * min(sH_cp1_base, sH_cp2_base), 0.5 * (sH_cp1_base + sH_cp2_base))
                    sH_cp_sobo = sH_cp_base * 1.0
                    sH_cp_cx = sH_cp_base * ZR

                    psi_bd_calc = 0.5 * psiba * (u + 1)
                    is_hard = (HB1 > 350 and HB2 > 350)
                    T_KHb = TABLE_HARD_KHB if is_hard else TABLE_SOFT_KHB
                    T_KFb = TABLE_HARD_KFB if is_hard else TABLE_SOFT_KFB
                    
                    if bo_tri == 'chia': col_idx = 2
                    elif bo_tri == 'khong_doixung': col_idx = 3 if loai_br == 'thang' else 4
                    else: col_idx = 5 if loai_br == 'thang' else 6
                    
                    KHb_calc = interpolate_factor(T_KHb, psi_bd_calc, col_idx)
                    KFb_calc = interpolate_factor(T_KFb, psi_bd_calc, col_idx)
                    
                    KHb_use = KHb_user if k_mode == 'manual' else KHb_calc
                    KFb_use = KFb_user if k_mode == 'manual' else KFb_calc

                    Ka = 43 if loai_br == 'nghieng' else 49.5
                    aw_calc = Ka * (u + 1) * math.pow((T1 * KHb_use) / (sH_cp_sobo**2 * u * psiba), 1/3)
                    aw = int(round(aw_calc))
                    m = get_standard_module(m_coef * aw)
                    x1 = x2 = delta_y = 0
                    alpha_w_deg = 20.0

                    if loai_br == 'nghieng':
                        beta_rad_sb = math.radians(beta_sb_deg) 
                        z1_calc = (2 * aw * math.cos(beta_rad_sb)) / (m * (u + 1))
                        z1 = max(17, int(z1_calc))
                        z2 = round(z1 * u)
                        um = z2 / z1
                        
                        cos_beta = max(-1.0, min(1.0, (m * (z1 + z2)) / (2 * aw)))
                        if cos_beta == 1.0:
                            z2 = math.floor((2 * aw / m) - z1)
                            cos_beta = max(-1.0, min(1.0, (m * (z1 + z2)) / (2 * aw)))
                        beta_rad = math.acos(cos_beta)
                        beta_deg = math.degrees(beta_rad)
                        aw_thuc = aw
                        dw1 = 2 * aw_thuc / (um + 1)
                    else:
                        beta_rad = 0
                        beta_deg = 0
                        z1_calc = (2 * aw) / (m * (u + 1))
                        z1 = max(17, int(z1_calc))
                        z2 = round(z1 * u)
                        um = z2 / z1
                        
                        a = m * (z1 + z2) / 2
                        if aw > a:
                            aw_thuc = aw
                            alpha = math.radians(20)
                            cos_alpha_w = a / aw_thuc * math.cos(alpha)
                            alpha_w = math.acos(cos_alpha_w)
                            alpha_w_deg = math.degrees(alpha_w)
                            inv_alpha = math.tan(alpha) - alpha
                            inv_alpha_w = math.tan(alpha_w) - alpha_w
                            xt = ((z1 + z2) / 2) * (inv_alpha_w - inv_alpha) / math.tan(alpha)
                            y = (aw_thuc - a) / m
                            delta_y = xt - y
                            x1 = xt / 2 
                            x2 = xt - x1
                        else:
                            aw_thuc = a
                            alpha_w_deg = 20.0
                            x1 = x2 = delta_y = 0
                            
                        dw1 = 2 * aw_thuc / (um + 1)

                    delta_u = abs(um - u) / u * 100
                    check_u = "ĐẠT" if delta_u <= 4 else "KHÔNG ĐẠT (> 4%)"
                    aw = aw_thuc
                    bw2 = round(psiba * aw)
                    bw1 = bw2 + 4
                    
                    ZM = 274
                    if loai_br == 'thang':
                        eps_alpha = (1.88 - 3.2*(1/z1 + 1/z2))
                        Zeps = math.sqrt((4 - eps_alpha) / 3); ZH = 1.76
                    else:
                        eps_alpha = (1.88 - 3.2*(1/z1 + 1/z2)) * math.cos(beta_rad)
                        Zeps = math.sqrt(1 / eps_alpha); ZH = 1.74 
                    
                    KH = KHb_use * 1.13 * 1.03
                    sH_thuc = ZM * ZH * Zeps * math.sqrt((2 * T1 * KH * (um + 1)) / (bw2 * (dw1**2) * um))
                    check_sH = "ĐẠT" if sH_thuc <= sH_cp_cx else "KHÔNG ĐẠT"
                    color_sH = "success" if sH_thuc <= sH_cp_cx else "highlight"

                    d1 = m * z1 / math.cos(beta_rad)
                    d2 = m * z2 / math.cos(beta_rad)
                    da1 = d1 + 2*m*(1 + x1 - delta_y)
                    da2 = d2 + 2*m*(1 + x2 - delta_y)
                    df1 = d1 - 2*m*(1.25 - x1)
                    df2 = d2 - 2*m*(1.25 - x2)
                    Ft = 2 * T1 / dw1
                    Fr = Ft * math.tan(math.radians(20)) / math.cos(beta_rad)
                    Fa = Ft * math.tan(beta_rad)

                    aw_suggestion_html, need_recalc = "", False
                    if sH_thuc > sH_cp_cx:
                        error_pct = ((sH_thuc - sH_cp_cx) / sH_cp_cx) * 100
                        if error_pct <= 20: 
                            need_recalc = True
                            aw_new_calc = aw * math.pow((sH_thuc / sH_cp_cx)**2, 1/3)
                            aw_new = int(round(aw_new_calc))
                            if aw_new <= aw: aw_new = aw + 1
                            if aw_new % 2 != 0: aw_new += 1 
                            
                            for _ in range(15): 
                                m_new = get_standard_module(m_coef * aw_new)
                                x1_new = x2_new = delta_y_new = 0
                                alpha_w_deg_new = 20.0
                                
                                if loai_br == 'nghieng':
                                    z1_calc_new = (2 * aw_new * math.cos(math.radians(beta_sb_deg))) / (m_new * (u + 1))
                                    z1_new = max(17, int(z1_calc_new))
                                    z2_new = round(z1_new * u)
                                    um_new = z2_new / z1_new
                                    
                                    cos_beta_new = max(-1.0, min(1.0, (m_new * (z1_new + z2_new)) / (2 * aw_new)))
                                    if cos_beta_new == 1.0:
                                        z2_new = math.floor((2 * aw_new / m_new) - z1_new)
                                        cos_beta_new = max(-1.0, min(1.0, (m_new * (z1_new + z2_new)) / (2 * aw_new)))
                                    beta_rad_new = math.acos(cos_beta_new)
                                    beta_deg_new = math.degrees(beta_rad_new)
                                    aw_thuc_new = aw_new
                                    dw1_new = 2 * aw_thuc_new / (um_new + 1)
                                else:
                                    beta_rad_new = 0
                                    beta_deg_new = 0
                                    z1_calc_new = (2 * aw_new) / (m_new * (u + 1))
                                    z1_new = max(17, int(z1_calc_new))
                                    z2_new = round(z1_new * u)
                                    um_new = z2_new / z1_new
                                    
                                    a_new = m_new * (z1_new + z2_new) / 2
                                    if aw_new > a_new:
                                        aw_thuc_new = aw_new
                                        alpha = math.radians(20)
                                        cos_alpha_w = a_new / aw_thuc_new * math.cos(alpha)
                                        alpha_w = math.acos(cos_alpha_w)
                                        alpha_w_deg_new = math.degrees(alpha_w)
                                        inv_alpha = math.tan(alpha) - alpha
                                        inv_alpha_w = math.tan(alpha_w) - alpha_w
                                        xt = ((z1_new + z2_new) / 2) * (inv_alpha_w - inv_alpha) / math.tan(alpha)
                                        y = (aw_thuc_new - a_new) / m_new
                                        delta_y_new = xt - y
                                        x1_new = xt / 2
                                        x2_new = xt - x1_new
                                    else:
                                        aw_thuc_new = a_new
                                        alpha_w_deg_new = 20.0
                                        x1_new = x2_new = delta_y_new = 0
                                        
                                    dw1_new = 2 * aw_thuc_new / (um_new + 1)

                                bw2_new = round(psiba * aw_thuc_new)
                                bw1_new = bw2_new + 4
                                
                                if loai_br == 'thang':
                                    eps_alpha_new = (1.88 - 3.2*(1/z1_new + 1/z2_new))
                                    Zeps_new = math.sqrt((4 - eps_alpha_new) / 3); ZH_new = 1.76
                                else:
                                    eps_alpha_new = (1.88 - 3.2*(1/z1_new + 1/z2_new)) * math.cos(beta_rad_new)
                                    Zeps_new = math.sqrt(1 / eps_alpha_new); ZH_new = 1.74 
                                
                                sH_thuc_new = ZM * ZH_new * Zeps_new * math.sqrt((2 * T1 * KH * (um_new + 1)) / (bw2_new * (dw1_new**2) * um_new))
                                
                                if sH_thuc_new <= sH_cp_cx:
                                    aw_new = aw_thuc_new
                                    break 
                                else: aw_new = aw_thuc_new + 2 

                            aw_suggestion_html = f"""
                            <tr><td colspan="3" style="background-color:#fef3c7; color:#b45309; padding:15px;">
                                <b>⚠️ BÁO CÁO CỦA VÒNG LẶP MÔ PHỎNG:</b><br>
                                Do ứng suất sinh ra ({sH_thuc:.1f} MPa) lớn hơn giới hạn chính xác ([σH] = {sH_cp_cx:.1f} MPa) (Vượt {error_pct:.1f}%).<br>
                                Công thức lặp nội suy: a<sub>w(mới)</sub> ≈ {aw} × ∛({sH_thuc:.1f}/{sH_cp_cx:.1f})² ≈ {aw_new_calc:.2f} mm.<br>
                                <b style="color:#047857;">Hệ thống đã tự động chạy vòng lặp tìm nghiệm chẵn và chốt a<sub>w</sub> = {aw_new:.1f} mm ở BẢNG 2!</b>
                            </td></tr>
                            """
                        else:
                            aw_suggestion_html = f"""
                            <tr><td colspan="3" style="background-color:#fee2e2; color:#b91c1c; padding:15px;">
                                <b>🚨 GIỚI HẠN ĐỎ (Độ chênh lệch {error_pct:.1f}% > 20%):</b><br>
                                Ứng suất tiếp xúc đang vượt quá xa mức chịu đựng của vật liệu. Hãy đổi Mác thép khác.
                            </td></tr>
                            """

                    img_b64 = draw_gear_schematic(d1, d2, aw, loai_br)
                    img_html = f'<div style="text-align:center; margin:20px 0;"><img src="data:image/png;base64,{img_b64}" style="max-width:100%; border:1px solid #cbd5e1; border-radius:8px;"></div>'

                    html_uon_quatai_b1 = ""
                    if not need_recalc:
                        YF1 = get_YF(z1 / (math.cos(beta_rad)**3)); YF2 = get_YF(z2 / (math.cos(beta_rad)**3))
                        Yeps = 1.0 if loai_br == 'thang' else 1 / eps_alpha
                        Ybeta = 1 - beta_deg / 140 if loai_br == 'nghieng' else 1
                        KF_thuc = KFb_use * 1.37 * 1.07 

                        sF1_thuc = (2 * T1 * KF_thuc * Yeps * Ybeta * YF1) / (bw1 * dw1 * m)
                        sF2_thuc = sF1_thuc * YF2 / YF1
                        
                        check_sF1 = "ĐẠT" if sF1_thuc <= sF_cp1 else "KHÔNG ĐẠT"
                        check_sF2 = "ĐẠT" if sF2_thuc <= sF_cp2 else "KHÔNG ĐẠT"

                        sH_max = sH_thuc * math.sqrt(Kqt)
                        sF1_max = sF1_thuc * Kqt
                        sF2_max = sF2_thuc * Kqt
                        
                        check_sH_max = "ĐẠT" if sH_max <= sH_max_cp else "KHÔNG ĐẠT"
                        check_sF1_max = "ĐẠT" if sF1_max <= sF1_max_cp else "KHÔNG ĐẠT"
                        check_sF2_max = "ĐẠT" if sF2_max <= sF2_max_cp else "KHÔNG ĐẠT"

                        html_uon_quatai_b1 = f"""
                        <tr><td colspan="3" class="step-title">BƯỚC 6: KIỂM NGHIỆM ĐỘ BỀN UỐN MỎI</td></tr>
                        <tr><th>Ứng suất uốn Bánh 1 (σF1)</th><td><b style="color:#047857;">{sF1_thuc:.1f} MPa</b></td><td class="{'success' if sF1_thuc<=sF_cp1 else 'highlight'}">{check_sF1} (≤ {sF_cp1:.1f})</td></tr>
                        <tr><th>Ứng suất uốn Bánh 2 (σF2)</th><td><b style="color:#047857;">{sF2_thuc:.1f} MPa</b></td><td class="{'success' if sF2_thuc<=sF_cp2 else 'highlight'}">{check_sF2} (≤ {sF_cp2:.1f})</td></tr>
                        <tr><td colspan="3" class="step-title">BƯỚC 7: KIỂM NGHIỆM QUÁ TẢI (TĨNH)</td></tr>
                        <tr><th>Quá tải Tiếp xúc (σHmax)</th><td><b style="color:#047857;">{sH_max:.1f} MPa</b></td><td class="{'success' if sH_max<=sH_max_cp else 'highlight'}">{check_sH_max} (≤ {sH_max_cp:.1f})</td></tr>
                        <tr><th>Quá tải Uốn B1 (σF1max)</th><td><b style="color:#047857;">{sF1_max:.1f} MPa</b></td><td class="{'success' if sF1_max<=sF1_max_cp else 'highlight'}">{check_sF1_max} (≤ {sF1_max_cp:.1f})</td></tr>
                        <tr><th>Quá tải Uốn B2 (σF2max)</th><td><b style="color:#047857;">{sF2_max:.1f} MPa</b></td><td class="{'success' if sF2_max<=sF2_max_cp else 'highlight'}">{check_sF2_max} (≤ {sF2_max_cp:.1f})</td></tr>
                        <tr><td colspan="3" class="step-title">BƯỚC 8 & 9: TỔNG KẾT KÍCH THƯỚC CHẾ TẠO VÀ LỰC</td></tr>
                        <tr><th>Chiều rộng vành răng (bw1 / bw2)</th><td><b style="color:#1d4ed8;">{bw1:.0f} / {bw2:.0f} mm</b></td><td>Bánh nhỏ làm rộng hơn 4mm</td></tr>
                        <tr><th>Đường kính chia (d1 / d2)</th><td>{d1:.2f} / {d2:.2f} mm</td><td>d = m.z / cosβ</td></tr>
                        <tr><th>Đường kính vòng đỉnh (da1 / da2)</th><td>{da1:.2f} / {da2:.2f} mm</td><td>da = d + 2m(1 + x - Δy)</td></tr>
                        <tr><th>Đường kính vòng chân (df1 / df2)</th><td>{df1:.2f} / {df2:.2f} mm</td><td>df = d - 2m(1.25 - x)</td></tr>
                        <tr><th>Lực ăn khớp (Ft / Fr / Fa)</th><td><b style="color:#d97706;">{Ft:,.0f} N / {Fr:,.0f} N / {Fa:,.0f} N</b></td><td>Dùng để tính ổ bi trục</td></tr>
                        """

                    html_dich_chinh_b1 = f"<tr><th>Hệ số dịch chỉnh (x1 / x2)</th><td><b style='color:#d97706;'>{x1:.3f} / {x2:.3f}</b></td><td>Góc ăn khớp αw = {alpha_w_deg:.2f}°</td></tr>" if loai_br == 'thang' and (x1 != 0 or x2 != 0) else ""

                    result_html = f"""
                    <div class="gen-theme">
                    <h2 style="text-align:center; color:#1e3a8a;">BẢNG 1: TÍNH NHÁP SƠ BỘ (a<sub>w</sub> = {aw:.1f} mm)</h2>
                    {img_html}
                    <table>
                        <tr><td colspan="3" class="step-title">BƯỚC 1: VẬT LIỆU BÁNH RĂNG</td></tr>
                        <tr><th>Mác thép & Độ cứng</th><td>B1: {mat1['name']} ({mat1['hard_type']} {b1_hard_val})<br>B2: {mat2['name']} ({mat2['hard_type']} {b2_hard_val})</td><td><span class="{mat_color}">{mat_check}</span></td></tr>
                        <tr><th>Tiếp xúc Cơ sở ([σH1] / [σH2])</th><td>{sH_cp1_base:.1f} / {sH_cp2_base:.1f} MPa</td><td>Chưa tính độ nhám ZR</td></tr>
                        <tr><th>Tiếp xúc CHUNG ([σH])</th><td>Sơ bộ: <b>{sH_cp_sobo:.1f}</b> | K.nghiệm: <b style="color:#b91c1c;">{sH_cp_cx:.1f}</b> MPa</td><td>Áp dụng ZR = {ZR}</td></tr>
                        <tr><th>Uốn cho phép ([σF1] / [σF2])</th><td>{sF_cp1:.1f} / {sF_cp2:.1f} MPa</td><td>Từ Bảng 6.2</td></tr>
                        <tr><td colspan="3" class="step-title">BƯỚC 3 & 4: KÍCH THƯỚC CƠ BẢN & ĐỘNG HỌC</td></tr>
                        <tr><th>Khoảng cách trục (aw)</th><td><b style="color:#1d4ed8; font-size:1.1em;">{aw:.1f} mm</b></td><td>Làm tròn chuẩn từ {aw_calc:.2f} mm</td></tr>
                        <tr><th>Mô đun tiêu chuẩn (m)</th><td><b>{m} mm</b></td><td>Tính theo hệ số m_coef = {m_coef}</td></tr>
                        <tr><th>Số răng (z1 / z2)</th><td><b>{z1} / {z2} răng</b></td><td>-</td></tr>
                        {html_dich_chinh_b1}
                        <tr><th>Sai số Tỉ số truyền (Δu)</th><td>{delta_u:.2f} %</td><td class="{'success' if delta_u<=4 else 'highlight'}">{check_u}</td></tr>
                        <tr><th>Góc nghiêng thực tế (β)</th><td><b style="color:#d97706;">{beta_deg:.2f} độ</b></td><td>Tính chính xác từ β sơ bộ</td></tr>
                        <tr><td colspan="3" class="step-title">BƯỚC 5: KIỂM NGHIỆM BỀN MỎI TIẾP XÚC</td></tr>
                        <tr><th>Ứng suất tiếp xúc thực tế (σH)</th><td><b style="color:#047857;">{sH_thuc:.1f} MPa</b></td><td class="{color_sH}">{check_sH} (So với {sH_cp_cx:.1f})</td></tr>
                        {aw_suggestion_html}
                        {html_uon_quatai_b1}
                    </table>
                    </div>
                    """

                    if need_recalc:
                        YF1_new = get_YF(z1_new / (math.cos(beta_rad_new)**3)); YF2_new = get_YF(z2_new / (math.cos(beta_rad_new)**3))
                        Yeps_new = 1.0 if loai_br == 'thang' else 1 / eps_alpha_new
                        Ybeta_new = 1 - beta_deg_new / 140 if loai_br == 'nghieng' else 1
                        KF_loop = KFb_use * 1.37 * 1.07
                        
                        sF1_thuc_new = (2 * T1 * KF_loop * Yeps_new * Ybeta_new * YF1_new) / (bw1_new * dw1_new * m_new)
                        sF2_thuc_new = sF1_thuc_new * YF2_new / YF1_new
                        
                        check_sF1_new = "ĐẠT" if sF1_thuc_new <= sF_cp1 else "KHÔNG ĐẠT"
                        check_sF2_new = "ĐẠT" if sF2_thuc_new <= sF_cp2 else "KHÔNG ĐẠT"

                        sH_max_new = sH_thuc_new * math.sqrt(Kqt); sF1_max_new = sF1_thuc_new * Kqt; sF2_max_new = sF2_thuc_new * Kqt
                        check_sH_max_new = "ĐẠT" if sH_max_new <= sH_max_cp else "KHÔNG ĐẠT"
                        check_sF1_max_new = "ĐẠT" if sF1_max_new <= sF1_max_cp else "KHÔNG ĐẠT"
                        check_sF2_max_new = "ĐẠT" if sF2_max_new <= sF2_max_cp else "KHÔNG ĐẠT"

                        d1_new = m_new * z1_new / math.cos(beta_rad_new); d2_new = m_new * z2_new / math.cos(beta_rad_new)
                        da1_new = d1_new + 2*m_new*(1 + x1_new - delta_y_new); da2_new = d2_new + 2*m_new*(1 + x2_new - delta_y_new)
                        df1_new = d1_new - 2*m_new*(1.25 - x1_new); df2_new = d2_new - 2*m_new*(1.25 - x2_new)
                        Ft_new = 2 * T1 / dw1_new; Fr_new = Ft_new * math.tan(math.radians(20)) / math.cos(beta_rad_new); Fa_new = Ft_new * math.tan(beta_rad_new)

                        html_dich_chinh_b2 = f"<tr><th>Hệ số dịch chỉnh (x1 / x2)</th><td><b style='color:#047857;'>{x1_new:.3f} / {x2_new:.3f}</b></td><td>Góc ăn khớp αw = {alpha_w_deg_new:.2f}°</td></tr>" if loai_br == 'thang' and (x1_new != 0 or x2_new != 0) else ""

                        img_b64_new = draw_gear_schematic(d1_new, d2_new, aw_new, loai_br)
                        img_html_new = f'<div style="text-align:center; margin:20px 0;"><img src="data:image/png;base64,{img_b64_new}" style="max-width:100%; border:1px solid #10b981; border-radius:8px;"></div>'

                        result_html += f"""
                        <div class="gen-theme">
                        <br><hr style="border-top: 2px dashed #10b981; margin: 40px 0;">
                        <h2 style="text-align:center; color:#047857;">BẢNG 2: KẾT QUẢ KIỂM NGHIỆM CHÍNH THỨC (a<sub>w</sub> = {aw_new:.1f} mm)</h2>
                        {img_html_new}
                        <table>
                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">KÍCH THƯỚC CƠ BẢN ĐƯỢC CẬP NHẬT</td></tr>
                            <tr><th>Khoảng cách trục (aw)</th><td><b style="color:#047857; font-size:1.1em;">{aw_new:.1f} mm</b></td><td>Từ vòng lặp tự động sửa lỗi</td></tr>
                            <tr><th>Mô đun tiêu chuẩn (m)</th><td><b>{m_new} mm</b></td><td>Tính theo hệ số m_coef = {m_coef}</td></tr>
                            <tr><th>Số răng (z1 / z2)</th><td><b>{z1_new} / {z2_new} răng</b></td><td>Đã phân bổ lại</td></tr>
                            {html_dich_chinh_b2}
                            <tr><th>Góc nghiêng thực tế (β)</th><td><b style="color:#047857;">{beta_deg_new:.2f} độ</b></td><td>Góc nghiêng sau điều chỉnh</td></tr>
                            
                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">BƯỚC 5 & 6: KIỂM NGHIỆM BỀN MỎI LẦN 2</td></tr>
                            <tr><th>Ứng suất tiếp xúc (σH)</th><td><b style="color:#047857;">{sH_thuc_new:.1f} MPa</b></td><td class="{'success' if sH_thuc_new<=sH_cp_cx else 'highlight'}">ĐẠT (≤ {sH_cp_cx:.1f})</td></tr>
                            <tr><th>Ứng suất uốn Bánh 1 (σF1)</th><td><b style="color:#047857;">{sF1_thuc_new:.1f} MPa</b></td><td class="{'success' if sF1_thuc_new<=sF_cp1 else 'highlight'}">{check_sF1_new} (≤ {sF_cp1:.1f})</td></tr>
                            <tr><th>Ứng suất uốn Bánh 2 (σF2)</th><td><b style="color:#047857;">{sF2_thuc_new:.1f} MPa</b></td><td class="{'success' if sF2_thuc_new<=sF_cp2 else 'highlight'}">{check_sF2_new} (≤ {sF_cp2:.1f})</td></tr>

                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">BƯỚC 7: KIỂM NGHIỆM QUÁ TẢI LẦN 2</td></tr>
                            <tr><th>Quá tải Tiếp xúc (σHmax)</th><td><b style="color:#047857;">{sH_max_new:.1f} MPa</b></td><td class="{'success' if sH_max_new<=sH_max_cp else 'highlight'}">{check_sH_max_new} (≤ {sH_max_cp:.1f})</td></tr>
                            <tr><th>Quá tải Uốn B1 (σF1max)</th><td><b style="color:#047857;">{sF1_max_new:.1f} MPa</b></td><td class="{'success' if sF1_max_new<=sF1_max_cp else 'highlight'}">{check_sF1_max_new} (≤ {sF1_max_cp:.1f})</td></tr>
                            <tr><th>Quá tải Uốn B2 (σF2max)</th><td><b style="color:#047857;">{sF2_max_new:.1f} MPa</b></td><td class="{'success' if sF2_max_new<=sF2_max_cp else 'highlight'}">{check_sF2_max_new} (≤ {sF2_max_cp:.1f})</td></tr>

                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">TỔNG KẾT CHẾ TẠO VÀ LỰC MỚI</td></tr>
                            <tr><th>Chiều rộng vành răng (bw1 / bw2)</th><td><b style="color:#047857;">{bw1_new:.0f} / {bw2_new:.0f} mm</b></td><td>Đã tính lại</td></tr>
                            <tr><th>Đường kính chia (d1 / d2)</th><td>{d1_new:.2f} / {d2_new:.2f} mm</td><td>d = m.z / cosβ</td></tr>
                            <tr><th>Đường kính vòng đỉnh (da1 / da2)</th><td>{da1_new:.2f} / {da2_new:.2f} mm</td><td>da = d + 2m(1 + x - Δy)</td></tr>
                            <tr><th>Đường kính vòng chân (df1 / df2)</th><td>{df1_new:.2f} / {df2_new:.2f} mm</td><td>df = d - 2m(1.25 - x)</td></tr>
                            <tr><th>Lực ăn khớp (Ft / Fr / Fa)</th><td><b style="color:#d97706;">{Ft_new:,.0f} N / {Fr_new:,.0f} N / {Fa_new:,.0f} N</b></td><td>Đã tính toán lại chuẩn xác</td></tr>
                        </table>
                        </div>
                        """

                elif loai_br == 'con_thang':
                    sH_cp_base = min(sH_cp1_base, sH_cp2_base)
                    sH_cp_sobo = sH_cp_base * 1.0
                    sH_cp_cx = sH_cp_base * ZR
                    KHb_use = KHb_user if k_mode == 'manual' else 1.15 
                    KFb_use = KFb_user if k_mode == 'manual' else 1.31
                    theta_Re = psiba 
                    
                    Re_calc = 50 * math.sqrt(u**2 + 1) * math.pow((T1 * KHb_use) / ((1 - theta_Re) * theta_Re * u * sH_cp_sobo**2), 1/3)
                    Re_sobo = round(Re_calc, 2)
                    de1_calc = 2 * Re_sobo / math.sqrt(1 + u**2)
                    z1p = max(10, int(de1_calc / 4.5))
                    z1_raw = 1.6 * z1p if HB1 < 350 else 1.3 * z1p
                    z1_temp = round(z1_raw)
                    dm1_calc = (1 - 0.5 * theta_Re) * de1_calc
                    mtm_calc = dm1_calc / z1_temp
                    mte_calc = mtm_calc / (1 - 0.5 * theta_Re)
                    mte = get_standard_module(mte_calc) 
                    mtm = mte * (1 - 0.5 * theta_Re)
                    z1 = round(dm1_calc / mtm)
                    z2 = round(u * z1)
                    um = z2 / z1
                    delta_u = abs(um - u) / u * 100 
                    
                    delta1_rad = math.atan(1 / um)
                    delta2_rad = math.pi/2 - delta1_rad
                    delta1_deg = math.degrees(delta1_rad)
                    delta2_deg = math.degrees(delta2_rad)
                    
                    x1 = 0.4 if um >= 3 else 0.3; x2 = -x1
                    xe1 = x1; xe2 = x2
                    dm1 = z1 * mtm
                    Re_thuc = 0.5 * mte * math.sqrt(z1**2 + z2**2)
                    b = round(theta_Re * Re_thuc, 2)
                    
                    zv1 = z1 / math.cos(delta1_rad); zv2 = z2 / math.cos(delta2_rad)
                    eps_alpha = 1.88 - 3.2*(1/z1 + 1/z2)
                    Zeps = math.sqrt((4 - eps_alpha) / 3)
                    ZM = 274; ZH = 1.76
                    
                    v = math.pi * dm1 * n1 / 60000
                    vH = 0.006 * 56 * v * math.sqrt(dm1 * (um + 1) / um)
                    KHv = 1 + vH * b * dm1 / (2 * T1 * KHb_use * 1.0)
                    KH = KHb_use * 1.0 * KHv
                    
                    sH_thuc = ZM * ZH * Zeps * math.sqrt((2 * T1 * KH * math.sqrt(um**2 + 1)) / (0.85 * b * (dm1**2) * um))
                    check_sH = "ĐẠT" if sH_thuc <= sH_cp_cx else "KHÔNG ĐẠT"
                    color_sH = "success" if sH_thuc <= sH_cp_cx else "highlight"

                    b_old = b; b_msg_html = ""
                    if sH_thuc > sH_cp_cx:
                        error_pct = ((sH_thuc - sH_cp_cx) / sH_cp_cx) * 100
                        if error_pct <= 5.0:
                            b_new_calc = b_old * (sH_thuc / sH_cp_cx)**2
                            b_new = int(math.ceil(b_new_calc))
                            theta_Re_new = b_new / Re_thuc
                            if theta_Re_new <= 0.3:
                                b = b_new
                                sH_thuc = sH_thuc * math.sqrt(b_old / b)
                                check_sH = "ĐẠT (Sau khi tăng b)"
                                color_sH = "success"
                                b_msg_html = f"<tr><td colspan='3' style='background-color:#fef3c7; color:#b45309; padding:15px;'>Đã tự động tăng chiều rộng vành răng từ {b_old} mm lên {b} mm.</td></tr>"
                            else: b_msg_html = f"<tr><td colspan='3' style='background-color:#fee2e2; color:#b91c1c; padding:15px;'>🚨 CẢNH BÁO: Phải tăng Re!</td></tr>"
                        else: b_msg_html = f"<tr><td colspan='3' style='background-color:#fee2e2; color:#b91c1c; padding:15px;'>🚨 CẢNH BÁO ĐỎ: Ứng suất vượt {error_pct:.1f}%</td></tr>"

                    YF1 = get_YF(zv1); YF2 = get_YF(zv2)
                    vF = 0.016 * 56 * v * math.sqrt(dm1 * (um + 1) / um)
                    KFv = 1 + vF * b * dm1 / (2 * T1 * KFb_use * 1.0)
                    KF = KFb_use * 1.0 * KFv 
                    sF1_thuc = (2 * T1 * KF * (1 / eps_alpha) * 1.0 * YF1) / (0.85 * b * mtm * dm1)
                    sF2_thuc = sF1_thuc * YF2 / YF1
                    
                    sH_max = sH_thuc * math.sqrt(Kqt); sF1_max = sF1_thuc * Kqt; sF2_max = sF2_thuc * Kqt

                    de1 = mte * z1; de2 = mte * z2
                    hae1 = mte * (1 + xe1); hae2 = mte * (1 + xe2)
                    hfe1 = mte * (1.2 - xe1); hfe2 = mte * (1.2 - xe2)
                    he = hae1 + hfe1
                    
                    da1 = de1 + 2 * hae1 * math.cos(delta1_rad)
                    da2 = de2 + 2 * hae2 * math.cos(delta2_rad)
                    df1 = de1 - 2 * hfe1 * math.cos(delta1_rad) 
                    df2 = de2 - 2 * hfe2 * math.cos(delta2_rad) 

                    Ft1 = 2 * T1 / dm1
                    Fr1 = Ft1 * math.tan(math.radians(20)) * math.cos(delta1_rad)
                    Fa1 = Ft1 * math.tan(math.radians(20)) * math.sin(delta1_rad)

                    img_b64 = draw_gear_schematic(de1, de2, Re_thuc, loai_br, mte=mte, b=b)
                    img_html = f'<div style="text-align:center; margin:20px 0;"><img src="data:image/png;base64,{img_b64}" style="max-width:100%; border:1px solid #cbd5e1; border-radius:8px;"></div>'

                    result_html = f"""
                    <div class="gen-theme">
                    <h2 style="text-align:center; color:#1e3a8a;">KẾT QUẢ THIẾT KẾ: BÁNH RĂNG CÔN THẲNG (R<sub>e</sub> = {Re_thuc:.2f} mm)</h2>
                    {img_html}
                    <table>
                        <tr><td colspan="3" class="step-title">BƯỚC 1 & 2: VẬT LIỆU VÀ ỨNG SUẤT</td></tr>
                        <tr><th>Mác thép & Độ cứng</th><td>B1: {mat1['name']} ({mat1['hard_type']} {b1_hard_val})<br>B2: {mat2['name']} ({mat2['hard_type']} {b2_hard_val})</td><td><span class="{mat_color}">{mat_check}</span></td></tr>
                        <tr><th>Tiếp xúc Cơ sở ([σH1] / [σH2])</th><td>{sH_cp1_base:.1f} / {sH_cp2_base:.1f} MPa</td><td>Chưa tính độ nhám ZR</td></tr>
                        <tr><th>Tiếp xúc CHUNG ([σH])</th><td><b style="color:#b91c1c;">{sH_cp_cx:.1f}</b> MPa</td><td>Lấy MIN của 2 bánh</td></tr>
                        <tr><th>Uốn cho phép ([σF1] / [σF2])</th><td>{sF_cp1:.1f} / {sF_cp2:.1f} MPa</td><td>Từ Bảng 6.2</td></tr>
                        
                        <tr><td colspan="3" class="step-title">BƯỚC 3 & 4: CHIỀU DÀI NÓN VÀ KÍCH THƯỚC HÌNH HỌC</td></tr>
                        <tr><th>Chiều dài nón ngoài (Re)</th><td><b style="color:#1d4ed8; font-size:1.1em;">{Re_thuc:.2f} mm</b></td><td>Tính lại từ tiêu chuẩn</td></tr>
                        <tr><th>Mô đun vòng ngoài (mte)</th><td><b>{mte} mm</b></td><td>Làm tròn chuẩn Bảng 6.8</td></tr>
                        <tr><th>Mô đun trung bình (mtm)</th><td>{mtm:.3f} mm</td><td>Tính tại tiết diện trung bình</td></tr>
                        <tr><th>Số răng (z1 / z2)</th><td><b>{z1} / {z2} răng</b></td><td>-</td></tr>
                        <tr><th>Tỉ số truyền thực tế (um)</th><td><b style="color:#d97706;">{um:.3f}</b></td><td>Từ z2/z1 (Sai số Δu = {delta_u:.2f}%)</td></tr>
                        <tr><th>Số răng tương đương (zv1 / zv2)</th><td>{zv1:.1f} / {zv2:.1f}</td><td>Dùng để tra bảng YF</td></tr>
                        <tr><th>Góc nón chia (δ1 / δ2)</th><td><b style="color:#d97706;">{delta1_deg:.2f}° / {delta2_deg:.2f}°</b></td><td>δ1 + δ2 = 90°</td></tr>
                        <tr><th>Chiều rộng vành răng (b)</th><td><b>{b} mm</b></td><td>b = Kbe × Re</td></tr>
                        
                        <tr><td colspan="3" class="step-title">BƯỚC 5: KIỂM NGHIỆM BỀN MỎI TIẾP XÚC</td></tr>
                        <tr><th>Ứng suất tiếp xúc thực tế (σH)</th><td><b style="color:#047857;">{sH_thuc:.1f} MPa</b></td><td class="{color_sH}">{check_sH} (So với {sH_cp_cx:.1f})</td></tr>
                        {b_msg_html}
                        
                        <tr><td colspan="3" class="step-title">BƯỚC 6: KIỂM NGHIỆM ĐỘ BỀN UỐN MỎI</td></tr>
                        <tr><th>Ứng suất uốn Bánh 1 (σF1)</th><td><b style="color:#047857;">{sF1_thuc:.1f} MPa</b></td><td class="{'success' if sF1_thuc<=sF_cp1 else 'highlight'}">{"ĐẠT" if sF1_thuc<=sF_cp1 else "KHÔNG ĐẠT"}</td></tr>
                        <tr><th>Ứng suất uốn Bánh 2 (σF2)</th><td><b style="color:#047857;">{sF2_thuc:.1f} MPa</b></td><td class="{'success' if sF2_thuc<=sF_cp2 else 'highlight'}">{"ĐẠT" if sF2_thuc<=sF_cp2 else "KHÔNG ĐẠT"}</td></tr>

                        <tr><td colspan="3" class="step-title">BƯỚC 7 & 8: TỔNG KẾT KÍCH THƯỚC CHẾ TẠO VÀ LỰC</td></tr>
                        <tr><th>Đường kính trung bình (dm1)</th><td>{dm1:.2f} mm</td><td>Tính lực tại trung bình</td></tr>
                        <tr><th>Đường kính vòng ngoài (de1/de2)</th><td>{de1:.2f} / {de2:.2f} mm</td><td>de = mte.z</td></tr>
                        <tr><th>Đường kính vòng đỉnh (da1/da2)</th><td>{da1:.2f} / {da2:.2f} mm</td><td>da = de + 2.hae.cos(δ)</td></tr>
                        <tr><th>Đường kính vòng chân (df1/df2)</th><td>{df1:.2f} / {df2:.2f} mm</td><td>df = de - 2.hfe.cos(δ)</td></tr>
                        
                        <tr><td colspan="3" class="step-title" style="background-color:#f59e0b !important;">THÔNG SỐ CHIỀU CAO RĂNG NGOÀI NÓN (CHẾ TẠO)</td></tr>
                        <tr><th>Hệ số dịch chỉnh (x1 / x2)</th><td><b style="color:#047857;">{xe1:.2f} / {xe2:.2f}</b></td><td>Tự động tra x1=0.4 khi u ≥ 3</td></tr>
                        <tr><th>Chiều cao răng ngoài (he)</th><td><b>{he:.2f} mm</b></td><td>he = 2.2 * mte</td></tr>
                        <tr><th>C.cao đầu răng ngoài (hae1 / hae2)</th><td>{hae1:.2f} / {hae2:.2f} mm</td><td>hae = mte * (1 + x)</td></tr>
                        <tr><th>C.cao chân răng ngoài (hfe1 / hfe2)</th><td>{hfe1:.2f} / {hfe2:.2f} mm</td><td>hfe = mte * (1.2 - x)</td></tr>

                        <tr><td colspan="3" class="step-title">TÍNH TOÁN LỰC TỔNG QUÁT (DÙNG CHO TRỤC)</td></tr>
                        <tr><th>Lực vòng trung bình (Ft1 = Ft2)</th><td><b style="color:#d97706;">{Ft1:,.0f} N</b></td><td>Đẩy vuông góc</td></tr>
                        <tr><th>Lực Hướng Tâm B1 / Dọc trục B2</th><td><b style="color:#d97706;">~ {Fr1:,.0f} N</b></td><td>Fr1 = Fa2</td></tr>
                        <tr><th>Lực Dọc Trục B1 / Hướng Tâm B2</th><td><b style="color:#d97706;">~ {Fa1:,.0f} N</b></td><td>Fa1 = Fr2</td></tr>
                    </table>
                    </div>
                    """

                elif loai_br == 'con_cong':
                    sH_cp_tb = 0.5 * (sH_cp1_base + sH_cp2_base)
                    sH_cp_min = min(sH_cp1_base, sH_cp2_base)
                    sH_cp_base = min(sH_cp_tb, 1.25 * sH_cp_min)
                    sH_cp_sobo = sH_cp_base * 1.0
                    sH_cp_cx = sH_cp_base * ZR
                    KHb_use = KHb_user if k_mode == 'manual' else 1.13 
                    KFb_use = KFb_user if k_mode == 'manual' else 1.28
                    
                    beta_m_deg = beta_sb_deg
                    beta_m_rad = math.radians(beta_m_deg)
                    Kbe = psiba 
                    KR = 41.75 
                    
                    Re_calc = KR * math.sqrt(u**2 + 1) * math.pow((T1 * KHb_use) / ((1 - Kbe) * Kbe * u * sH_cp_sobo**2), 1/3)
                    Re_sobo = round(Re_calc, 2)
                    de1_calc = 2 * Re_sobo / math.sqrt(u**2 + 1)
                    z1p = max(10, int(round(de1_calc / 4.8))) 
                    z1_raw = 1.6 * z1p if HB1 < 350 else 1.3 * z1p
                    z1_temp = round(z1_raw)
                    dm1_calc = (1 - 0.5 * Kbe) * de1_calc
                    mtm_calc = dm1_calc / z1_temp
                    mnm = get_standard_module(mtm_calc * math.cos(beta_m_rad)) 
                    mtm = mnm / math.cos(beta_m_rad)
                    z1 = round(dm1_calc / mtm); z2 = round(u * z1); um = z2 / z1
                    delta_u = abs(um - u) / u * 100 
                    
                    delta1_rad = math.atan(1 / um); delta2_rad = math.pi/2 - delta1_rad
                    delta1_deg = math.degrees(delta1_rad); delta2_deg = math.degrees(delta2_rad)
                    x1 = (2 * (1 - 1/(um**2)) * (math.cos(beta_m_rad)**3)) / z1 if z1 > 0 else 0
                    x2 = -x1; xe1 = x1; xe2 = x2
                    dm1 = z1 * mtm; mte = mtm / (1 - 0.5 * Kbe)
                    Re_thuc = 0.5 * mte * math.sqrt(z1**2 + z2**2)
                    b = round(Kbe * Re_thuc)
                    
                    zv1 = z1 / (math.cos(delta1_rad) * (math.cos(beta_m_rad)**3))
                    zv2 = z2 / (math.cos(delta2_rad) * (math.cos(beta_m_rad)**3))
                    eps_alpha = (1.88 - 3.2*(1/z1 + 1/z2)) * math.cos(beta_m_rad)
                    Zeps = math.sqrt(1 / eps_alpha); ZM = 274; ZH = 1.5
                    
                    v = math.pi * dm1 * n1 / 60000
                    KHa = 1.13
                    vH = 0.002 * 73 * v * math.sqrt(dm1 * (um + 1) / um) 
                    KHv = 1 + vH * b * dm1 / (2 * T1 * KHb_use * KHa)
                    KH = KHb_use * KHa * KHv
                    
                    sH_thuc = ZM * ZH * Zeps * math.sqrt((2 * T1 * KH * math.sqrt(um**2 + 1)) / (0.85 * b * (dm1**2) * um))
                    check_sH = "ĐẠT" if sH_thuc <= sH_cp_cx else "KHÔNG ĐẠT"
                    color_sH = "success" if sH_thuc <= sH_cp_cx else "highlight"

                    aw_suggestion_html = ""
                    b_msg_html = ""
                    need_recalc = False
                    
                    if sH_thuc > sH_cp_cx:
                        error_pct = ((sH_thuc - sH_cp_cx) / sH_cp_cx) * 100
                        if error_pct <= 5.0:
                            b_old = b
                            b_new = int(math.ceil(b * (sH_thuc / sH_cp_cx)**2))
                            if b_new % 2 != 0: b_new += 1
                            if b_new / Re_thuc <= 0.3:
                                sH_thuc = sH_thuc * math.sqrt(b / b_new)
                                b = b_new; check_sH = "ĐẠT (Sau khi tăng b)"; color_sH = "success"
                                b_msg_html = f"<tr><td colspan='3' style='background-color:#fef3c7; color:#b45309; padding:15px;'>Đã tự động tăng chiều rộng vành răng từ {b_old} mm lên {b} mm.</td></tr>"
                            else: need_recalc = True
                        else: need_recalc = True

                    if need_recalc:
                        Re_test = Re_thuc * math.pow((sH_thuc / sH_cp_cx), 2/3)
                        for loop_idx in range(15):
                            de1_calc_new = 2 * Re_test / math.sqrt(u**2 + 1)
                            z1p_new = max(10, int(round(de1_calc_new / 4.8)))
                            z1_temp_new = round(1.6 * z1p_new if HB1 < 350 else 1.3 * z1p_new)
                            dm1_calc_new = (1 - 0.5 * Kbe) * de1_calc_new
                            mnm_new = get_standard_module(dm1_calc_new / z1_temp_new * math.cos(beta_m_rad))
                            if loop_idx > 0 and mnm_new <= mnm:
                                std_m = [1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0, 16.0]
                                idx = std_m.index(mnm) if mnm in std_m else 0
                                if idx < len(std_m) - 1: mnm_new = std_m[idx+1]
                            mtm_new = mnm_new / math.cos(beta_m_rad)
                            z1_new = round(dm1_calc_new / mtm_new); z2_new = round(u * z1_new); um_new = z2_new / z1_new
                            dm1_new = z1_new * mtm_new; mte_new = mtm_new / (1 - 0.5 * Kbe)
                            Re_thuc_new = 0.5 * mte_new * math.sqrt(z1_new**2 + z2_new**2)
                            b_new = round(Kbe * Re_thuc_new)
                            if b_new % 2 != 0: b_new += 1
                            v_new = math.pi * dm1_new * n1 / 60000
                            KHv_new = 1 + (0.002 * 73 * v_new * math.sqrt(dm1_new * (um_new + 1) / um_new)) * b_new * dm1_new / (2 * T1 * KHb_use * 1.13)
                            eps_alpha_new = (1.88 - 3.2*(1/z1_new + 1/z2_new)) * math.cos(beta_m_rad)
                            sH_thuc_new = ZM * ZH * math.sqrt(1 / eps_alpha_new) * math.sqrt((2 * T1 * KHb_use * 1.13 * KHv_new * math.sqrt(um_new**2 + 1)) / (0.85 * b_new * (dm1_new**2) * um_new))
                            if sH_thuc_new <= sH_cp_cx: break
                            else: Re_test += 5.0 
                        
                        Re_need_disp = Re_thuc * math.pow((sH_thuc / sH_cp_cx), 2/3)
                        aw_suggestion_html = f"""
                        <tr><td colspan="3" style="background-color:#fef3c7; color:#b45309; padding:15px;">
                            <b>⚠️ BÁO CÁO CỦA VÒNG LẶP KIỂM NGHIỆM LẠI :</b><br>
                            Do ứng suất sinh ra ({sH_thuc:.1f} MPa) lớn hơn giới hạn chính xác ([σH] = {sH_cp_cx:.1f} MPa).<br>
                            Công thức lặp nội suy: Re(cần) ≈ {Re_thuc:.1f} × ({sH_thuc:.1f}/{sH_cp_cx:.1f})<sup>2/3</sup> ≈ {Re_need_disp:.2f} mm.<br>
                            <b style="color:#047857;">Hệ thống đã bỏ qua kiểm nghiệm Uốn ở bảng này, tự động chạy vòng lặp tìm Re chuẩn và chốt ở BẢNG 2!</b>
                        </td></tr>
                        """

                    img_b64 = draw_gear_schematic(mte*z1, mte*z2, Re_thuc, loai_br, mte=mte, b=b)
                    img_html = f'<div style="text-align:center; margin:20px 0;"><img src="data:image/png;base64,{img_b64}" style="max-width:100%; border:1px solid #cbd5e1; border-radius:8px;"></div>'

                    result_html = f"""
                    <div class="gen-theme">
                    <h2 style="text-align:center; color:#1e3a8a;">BẢNG 1: TÍNH NHÁP SƠ BỘ (R<sub>e</sub> = {Re_thuc:.2f} mm)</h2>
                    {img_html}
                    <table>
                        <tr><td colspan="3" class="step-title">BƯỚC 1 & 2: VẬT LIỆU VÀ ỨNG SUẤT</td></tr>
                        <tr><th>Mác thép & Độ cứng</th><td>B1: {mat1['name']} ({mat1['hard_type']} {b1_hard_val})<br>B2: {mat2['name']} ({mat2['hard_type']} {b2_hard_val})</td><td><span class="{mat_color}">{mat_check}</span></td></tr>
                        <tr><th>Tiếp xúc Cơ sở ([σH1] / [σH2])</th><td>{sH_cp1_base:.1f} / {sH_cp2_base:.1f} MPa</td><td>Chưa tính độ nhám ZR</td></tr>
                        <tr><th>Tiếp xúc CHUNG ([σH])</th><td><b style="color:#b91c1c;">{sH_cp_cx:.1f}</b> MPa</td><td>Tr.bình cộng (Khác nón thẳng)</td></tr>
                        <tr><th>Uốn cho phép ([σF1] / [σF2])</th><td>{sF_cp1:.1f} / {sF_cp2:.1f} MPa</td><td>Từ Bảng 6.2</td></tr>
                        
                        <tr><td colspan="3" class="step-title">BƯỚC 3 & 4: CHIỀU DÀI NÓN VÀ KÍCH THƯỚC HÌNH HỌC</td></tr>
                        <tr><th>Chiều dài nón ngoài (Re)</th><td><b style="color:#1d4ed8; font-size:1.1em;">{Re_thuc:.2f} mm</b></td><td>Tính lại từ tiêu chuẩn (KR={KR})</td></tr>
                        <tr><th>Mô đun P.Tuyến T.Bình (mnm)</th><td><b style="color:#047857;">{mnm} mm</b></td><td>Quy chuẩn theo tiêu chuẩn cắt Răng</td></tr>
                        <tr><th>Mô đun vòng ngoài (mte)</th><td><b>{mte:.3f} mm</b></td><td>Tính từ mtm</td></tr>
                        <tr><th>Số răng (z1 / z2)</th><td><b>{z1} / {z2} răng</b></td><td>-</td></tr>
                        <tr><th>Tỉ số truyền thực tế (um)</th><td><b style="color:#d97706;">{um:.3f}</b></td><td>Từ z2/z1 (Sai số Δu = {delta_u:.2f}%)</td></tr>
                        <tr><th>Góc xoắn trung bình (βm)</th><td><b style="color:#d97706;">{beta_m_deg:.1f}°</b></td><td>Nhập từ người dùng</td></tr>
                        <tr><th>Số răng tương đương (zv1 / zv2)</th><td>{zv1:.1f} / {zv2:.1f}</td><td>Dùng để tra bảng YF (Có chia cos³βm)</td></tr>
                        <tr><th>Góc nón chia (δ1 / δ2)</th><td><b style="color:#d97706;">{delta1_deg:.2f}° / {delta2_deg:.2f}°</b></td><td>δ1 + δ2 = 90°</td></tr>
                        <tr><th>Chiều rộng vành răng (b)</th><td><b>{b} mm</b></td><td>b = Kbe × Re</td></tr>
                        
                        <tr><td colspan="3" class="step-title">BƯỚC 5: KIỂM NGHIỆM BỀN MỎI TIẾP XÚC</td></tr>
                        <tr><th>Ứng suất tiếp xúc thực tế (σH)</th><td><b style="color:#047857;">{sH_thuc:.1f} MPa</b></td><td class="{color_sH}">{check_sH} (So với {sH_cp_cx:.1f})</td></tr>
                        {b_msg_html}
                        {aw_suggestion_html}
                    """

                    if not need_recalc:
                        YF1 = get_YF(zv1); YF2 = get_YF(zv2)
                        vF = 0.006 * 73 * v * math.sqrt(dm1 * (um + 1) / um) 
                        KFv = 1 + vF * b * dm1 / (2 * T1 * KFb_use * 1.37)
                        KF = KFb_use * 1.37 * KFv 
                        
                        Ybeta = 1 - beta_m_deg / 140
                        Yeps = 1 / eps_alpha
                        
                        sF1_thuc = (2 * T1 * KF * Yeps * Ybeta * YF1) / (0.85 * b * mnm * dm1)
                        sF2_thuc = sF1_thuc * YF2 / YF1
                        
                        sH_max = sH_thuc * math.sqrt(Kqt); sF1_max = sF1_thuc * Kqt; sF2_max = sF2_thuc * Kqt

                        hae1 = mte + xe1 * mnm; hae2 = mte + xe2 * mnm
                        hfe1 = 1.2 * mte - xe1 * mnm; hfe2 = 1.2 * mte - xe2 * mnm
                        he = hae1 + hfe1
                        
                        de1 = mte * z1; de2 = mte * z2
                        da1 = de1 + 2 * hae1 * math.cos(delta1_rad)
                        da2 = de2 + 2 * hae2 * math.cos(delta2_rad)
                        df1 = de1 - 2 * hfe1 * math.cos(delta1_rad)
                        df2 = de2 - 2 * hfe2 * math.cos(delta2_rad)

                        Ft1 = 2 * T1 / dm1
                        Fr1_ref = Ft1 * math.tan(math.radians(20)) * math.cos(delta1_rad) / math.cos(beta_m_rad)
                        Fa1_ref = Ft1 * math.tan(math.radians(20)) * math.sin(delta1_rad) / math.cos(beta_m_rad)

                        result_html += f"""
                        <tr><td colspan="3" class="step-title">BƯỚC 6: KIỂM NGHIỆM ĐỘ BỀN UỐN MỎI</td></tr>
                        <tr><th>Ứng suất uốn Bánh 1 (σF1)</th><td><b style="color:#047857;">{sF1_thuc:.1f} MPa</b></td><td class="{'success' if sF1_thuc<=sF_cp1 else 'highlight'}">{"ĐẠT" if sF1_thuc<=sF_cp1 else "KHÔNG ĐẠT"} (≤ {sF_cp1:.1f})</td></tr>
                        <tr><th>Ứng suất uốn Bánh 2 (σF2)</th><td><b style="color:#047857;">{sF2_thuc:.1f} MPa</b></td><td class="{'success' if sF2_thuc<=sF_cp2 else 'highlight'}">{"ĐẠT" if sF2_thuc<=sF_cp2 else "KHÔNG ĐẠT"} (≤ {sF_cp2:.1f})</td></tr>

                        <tr><td colspan="3" class="step-title">BƯỚC 7 & 8: TỔNG KẾT KÍCH THƯỚC CHẾ TẠO VÀ LỰC</td></tr>
                        <tr><th>Đường kính trung bình (dm1)</th><td>{dm1:.2f} mm</td><td>Tính lực tại trung bình</td></tr>
                        <tr><th>Đường kính vòng ngoài (de1/de2)</th><td>{de1:.2f} / {de2:.2f} mm</td><td>de = mte.z</td></tr>
                        <tr><th>Đường kính vòng đỉnh (da1/da2)</th><td>{da1:.2f} / {da2:.2f} mm</td><td>da = de + 2.hae.cos(δ)</td></tr>
                        <tr><th>Đường kính vòng chân (df1/df2)</th><td>{df1:.2f} / {df2:.2f} mm</td><td>df = de - 2.hfe.cos(δ)</td></tr>
                        
                        <tr><td colspan="3" class="step-title" style="background-color:#f59e0b !important;">THÔNG SỐ CHIỀU CAO RĂNG NGOÀI NÓN (CHẾ TẠO)</td></tr>
                        <tr><th>Hệ số dịch chỉnh (x1 / x2)</th><td><b style="color:#047857;">{x1:.3f} / {x2:.3f}</b></td><td>x1 = (2(1-1/u²).cos³β)/z1</td></tr>
                        <tr><th>Chiều cao răng ngoài tổng (he)</th><td><b>{he:.2f} mm</b></td><td>he = hae + hfe</td></tr>
                        <tr><th>C.cao đầu răng ngoài (hae1 / hae2)</th><td>{hae1:.2f} / {hae2:.2f} mm</td><td>hae = mte + x.mnm</td></tr>
                        <tr><th>C.cao chân răng ngoài (hfe1 / hfe2)</th><td>{hfe1:.2f} / {hfe2:.2f} mm</td><td>hfe = 1.2mte - x.mnm</td></tr>

                        <tr><td colspan="3" class="step-title">TÍNH TOÁN LỰC TỔNG QUÁT (DÙNG CHO TRỤC)</td></tr>
                        <tr><th>Lực vòng trung bình (Ft1 = Ft2)</th><td><b style="color:#d97706;">{Ft1:,.0f} N</b></td><td>Đẩy vuông góc</td></tr>
                        <tr><th>Lực Hướng Tâm B1 / Dọc trục B2</th><td><b style="color:#d97706;">~ {Fr1_ref:,.0f} N</b></td><td>(Độ lớn ước tính)</td></tr>
                        <tr><th>Lực Dọc Trục B1 / Hướng Tâm B2</th><td><b style="color:#d97706;">~ {Fa1_ref:,.0f} N</b></td><td>(Độ lớn ước tính)</td></tr>
                        """
                    result_html += "</table></div>"

                    if need_recalc:
                        xe1_new = (2 * (1 - 1/(um_new**2)) * (math.cos(beta_m_rad)**3)) / z1_new if z1_new > 0 else 0
                        delta1_rad_new = math.atan(1 / um_new)
                        delta2_rad_new = math.pi/2 - delta1_rad_new

                        zv1_new = z1_new / (math.cos(delta1_rad_new) * (math.cos(beta_m_rad)**3))
                        zv2_new = z2_new / (math.cos(delta2_rad_new) * (math.cos(beta_m_rad)**3))
                        YF1_new = get_YF(zv1_new); YF2_new = get_YF(zv2_new)
                        
                        vF_new = 0.006 * 73 * v_new * math.sqrt(dm1_new * (um_new + 1) / um_new)
                        KFv_new = 1 + vF_new * b_new * dm1_new / (2 * T1 * KFb_use * 1.37)
                        KF_loop = KFb_use * 1.37 * KFv_new
                        
                        Yeps_new = 1 / eps_alpha_new
                        Ybeta_new = 1 - beta_m_deg / 140
                        sF1_thuc_new = (2 * T1 * KF_loop * Yeps_new * Ybeta_new * YF1_new) / (0.85 * b_new * mnm_new * dm1_new)
                        sF2_thuc_new = sF1_thuc_new * YF2_new / YF1_new
                        
                        check_sF1_new = "ĐẠT" if sF1_thuc_new <= sF_cp1 else "KHÔNG ĐẠT"
                        check_sF2_new = "ĐẠT" if sF2_thuc_new <= sF_cp2 else "KHÔNG ĐẠT"

                        sH_max_new = sH_thuc_new * math.sqrt(Kqt); sF1_max_new = sF1_thuc_new * Kqt; sF2_max_new = sF2_thuc_new * Kqt

                        check_sH_max_new = "ĐẠT" if sH_max_new <= sH_max_cp else "KHÔNG ĐẠT"
                        check_sF1_max_new = "ĐẠT" if sF1_max_new <= sF1_max_cp else "KHÔNG ĐẠT"
                        check_sF2_max_new = "ĐẠT" if sF2_max_new <= sF2_max_cp else "KHÔNG ĐẠT"

                        hae1_new = mte_new + xe1_new * mnm_new; hae2_new = mte_new - xe1_new * mnm_new
                        hfe1_new = 1.2 * mte_new - xe1_new * mnm_new; hfe2_new = 1.2 * mte_new + xe1_new * mnm_new
                        he_new = hae1_new + hfe1_new
                        
                        de1_new = mte_new * z1_new; de2_new = mte_new * z2_new
                        da1_new = de1_new + 2 * hae1_new * math.cos(delta1_rad_new); da2_new = de2_new + 2 * hae2_new * math.cos(delta2_rad_new)
                        df1_new = de1_new - 2 * hfe1_new * math.cos(delta1_rad_new); df2_new = de2_new - 2 * hfe2_new * math.cos(delta2_rad_new)

                        Ft_new = 2 * T1 / dm1_new
                        Fr1_ref_new = Ft_new * math.tan(math.radians(20)) * math.cos(delta1_rad_new) / math.cos(beta_m_rad)
                        Fa1_ref_new = Ft_new * math.tan(math.radians(20)) * math.sin(delta1_rad_new) / math.cos(beta_m_rad)

                        img_b64_new = draw_gear_schematic(mte_new*z1_new, mte_new*z2_new, Re_thuc_new, loai_br, mte=mte_new, b=b_new)
                        img_html_new = f'<div style="text-align:center; margin:20px 0;"><img src="data:image/png;base64,{img_b64_new}" style="max-width:100%; border:1px solid #10b981; border-radius:8px;"></div>'

                        result_html += f"""
                        <div class="gen-theme">
                        <br><hr style="border-top: 2px dashed #10b981; margin: 40px 0;">
                        <h2 style="text-align:center; color:#047857;">BẢNG 2: KẾT QUẢ KIỂM NGHIỆM CHÍNH THỨC (R<sub>e</sub> = {Re_thuc_new:.1f} mm)</h2>
                        {img_html_new}
                        <table>
                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">BƯỚC 3 & 4: CHIỀU DÀI NÓN VÀ KÍCH THƯỚC ĐÃ CẬP NHẬT</td></tr>
                            <tr><th>Chiều dài nón ngoài (Re)</th><td><b style="color:#047857; font-size:1.1em;">{Re_thuc_new:.2f} mm</b></td><td>Từ vòng lặp tự động sửa lỗi</td></tr>
                            <tr><th>Mô đun P.Tuyến T.Bình (mnm)</th><td><b>{mnm_new} mm</b></td><td>Tính theo hệ số R<sub>e(cần)</sub></td></tr>
                            <tr><th>Mô đun vòng ngoài (mte)</th><td><b>{mte_new:.3f} mm</b></td><td>Đã tính lại từ mtm</td></tr>
                            <tr><th>Số răng (z1 / z2)</th><td><b>{z1_new} / {z2_new} răng</b></td><td>Đã phân bổ lại</td></tr>
                            <tr><th>Tỉ số truyền thực tế (um)</th><td><b style="color:#047857;">{um_new:.3f}</b></td><td>Sai số: {abs(um_new-u)/u*100:.2f}%</td></tr>
                            <tr><th>Góc nón chia (δ1 / δ2)</th><td><b style="color:#047857;">{math.degrees(delta1_rad_new):.2f}° / {math.degrees(delta2_rad_new):.2f}°</b></td><td>Đã tính lại</td></tr>
                            <tr><th>Chiều rộng vành răng (b)</th><td><b style="color:#047857;">{b_new} mm</b></td><td>Đã tính lại b = Kbe × Re_thuc</td></tr>
                            
                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">BƯỚC 5 & 6: KIỂM NGHIỆM BỀN MỎI LẦN 2</td></tr>
                            <tr><th>Ứng suất tiếp xúc (σH)</th><td><b style="color:#047857;">{sH_thuc_new:.1f} MPa</b></td><td class="{'success' if sH_thuc_new<=sH_cp_cx else 'highlight'}">ĐẠT (≤ {sH_cp_cx:.1f})</td></tr>
                            <tr><th>Ứng suất uốn Bánh 1 (σF1)</th><td><b style="color:#047857;">{sF1_thuc_new:.1f} MPa</b></td><td class="{'success' if sF1_thuc_new<=sF_cp1 else 'highlight'}">{check_sF1_new} (≤ {sF_cp1:.1f})</td></tr>
                            <tr><th>Ứng suất uốn Bánh 2 (σF2)</th><td><b style="color:#047857;">{sF2_thuc_new:.1f} MPa</b></td><td class="{'success' if sF2_thuc_new<=sF_cp2 else 'highlight'}">{check_sF2_new} (≤ {sF_cp2:.1f})</td></tr>

                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">BƯỚC 7: KIỂM NGHIỆM QUÁ TẢI (TĨNH) LẦN 2</td></tr>
                            <tr><th>Quá tải Tiếp xúc (σHmax)</th><td><b style="color:#047857;">{sH_max_new:.1f} MPa</b></td><td class="{'success' if sH_max_new<=sH_max_cp else 'highlight'}">{check_sH_max_new} (≤ {sH_max_cp:.1f})</td></tr>
                            <tr><th>Quá tải Uốn B1 (σF1max)</th><td><b style="color:#047857;">{sF1_max_new:.1f} MPa</b></td><td class="{'success' if sF1_max_new<=sF1_max_cp else 'highlight'}">{check_sF1_max_new} (≤ {sF1_max_cp:.1f})</td></tr>
                            <tr><th>Quá tải Uốn B2 (σF2max)</th><td><b style="color:#047857;">{sF2_max_new:.1f} MPa</b></td><td class="{'success' if sF2_max_new<=sF2_max_cp else 'highlight'}">{check_sF2_max_new} (≤ {sF2_max_cp:.1f})</td></tr>

                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">TỔNG KẾT CHẾ TẠO VÀ LỰC MỚI</td></tr>
                            <tr><th>Đường kính trung bình (dm1)</th><td>{dm1_new:.2f} mm</td><td>Tính tại tiết diện trung bình</td></tr>
                            <tr><th>Đường kính vòng ngoài (de1/de2)</th><td>{de1_new:.2f} / {de2_new:.2f} mm</td><td>Tính tại vòng ngoài</td></tr>
                            <tr><th>Đường kính vòng đỉnh (da1/da2)</th><td>{da1_new:.2f} / {da2_new:.2f} mm</td><td>da = de + 2.hae.cos(δ)</td></tr>
                            <tr><th>Đường kính vòng chân (df1/df2)</th><td>{df1_new:.2f} / {df2_new:.2f} mm</td><td>df = de - 2.hfe.cos(δ)</td></tr>
                            
                            <tr><td colspan="3" class="step-title" style="background-color:#f59e0b !important;">THÔNG SỐ CHIỀU CAO RĂNG MỚI</td></tr>
                            <tr><th>Hệ số dịch chỉnh (x1 / x2)</th><td><b style="color:#047857;">{xe1_new:.3f} / {-xe1_new:.3f}</b></td><td>Tính toán lại chính xác</td></tr>
                            <tr><th>Chiều cao răng ngoài tổng (he)</th><td><b style="color:#047857;">{he_new:.2f} mm</b></td><td>he = hae + hfe</td></tr>
                            <tr><th>C.cao đầu răng ngoài (hae)</th><td>{hae1_new:.2f} / {hae2_new:.2f} mm</td><td>hae = mte + x.mnm</td></tr>
                            <tr><th>C.cao chân răng ngoài (hfe)</th><td>{hfe1_new:.2f} / {hfe2_new:.2f} mm</td><td>hfe = 1.2mte - x.mnm</td></tr>
                            
                            <tr><td colspan="3" class="step-title" style="background-color:#10b981 !important;">TÍNH TOÁN LỰC LẠI</td></tr>
                            <tr><th>Lực vòng trung bình (Ft)</th><td><b style="color:#d97706;">{Ft_new:,.0f} N</b></td><td>Đẩy vuông góc</td></tr>
                            <tr><th>Lực Hướng Tâm / Dọc Trục B1</th><td><b style="color:#d97706;">~ {Fr1_ref_new:,.0f} N / {Fa1_ref_new:,.0f} N</b></td><td>Ước lượng mới</td></tr>
                        </table>
                        </div>
                        """

            except Exception as e:
                trace = traceback.format_exc()
                result_html = f"<div class='error-box'><b>Lỗi tính toán:</b> {str(e)}<br><span style='font-size:12px;color:#9ca3af;'>{trace}</span></div>"

        # =====================================================================
        # NHÁNH 2: XỬ LÝ ĐỘC LẬP CHO HÀNH TINH  
        # =====================================================================
        elif loai_br == 'hanh_tinh':
            try:
                # 1. LẤY TOÀN BỘ DỮ LIỆU INPUT HT
                Po = float(request.form.get('ht_Po', 15.7))
                n1 = float(request.form.get('ht_n1', 187.5))
                n0 = float(request.form.get('ht_n0', 37.5))
                c = int(request.form.get('ht_c', 3))
                Lh = float(request.form.get('ht_Lh', 5000))
                Kqt = float(request.form.get('ht_Kqt', 2.0))
                
                Kd = float(request.form.get('ht_Kd', 77))
                Kc_rang = float(request.form.get('ht_Kc_rang', 1.2))
                KH_Sigma = float(request.form.get('ht_KH_Sigma', 1.3))
                psiba = float(request.form.get('ht_psiba', 0.7))
                ZM = float(request.form.get('ht_ZM', 274))
                YF1 = float(request.form.get('ht_YF1', 4.13))
                YF2 = float(request.form.get('ht_YF2', 3.8))
                YF3 = float(request.form.get('ht_YF3', 3.35))
                
                C_kN = float(request.form.get('ht_C_kN', 64.9))
                Kc_o = float(request.form.get('ht_Kc_o', 1.1))
                V_olan = float(request.form.get('ht_V_olan', 1.2))
                s_olan = float(request.form.get('ht_s_olan', 1.3))

                kfc1 = float(request.form.get('ht_kfc_1', 1.0))
                kfc2 = float(request.form.get('ht_kfc_2', 0.75))
                kfc3 = float(request.form.get('ht_kfc_3', 1.0))

                # BƯỚC 1: ĐỘNG HỌC
                u10 = n1 / n0
                e_input = request.form.get('ht_e_val')
                e = float(e_input) if e_input else (u10 - 1)
                u12 = 0.5 * (e - 1)
                u23 = e / u12
                
                To = 9.55 * (10**6) * Po / n0
                T1 = To / (e + 1)
                T2 = T1 * u12 / c

                # BƯỚC 2: VẬT LIỆU VÀ ỨNG SUẤT
                b1_mat = HT_MATERIAL_DB[request.form.get('ht_b1_mat', '40XH_T')]
                b1_hard = float(request.form.get('ht_b1_hard_val', 52))
                b1_opt_idx = int(request.form.get('ht_b1_opt', 0))
                sch1 = b1_mat['options'][b1_opt_idx]['sch']
                
                b1_sh_0, b1_sf_0, sh1_sf, sf1_sf = calc_ht_stress(request.form.get('ht_b1_stress', 'f3'), b1_hard)
                HB1 = b1_hard if b1_mat['type'] == 'HB' else hrc_to_hb(b1_hard)
                
                b3_mat = HT_MATERIAL_DB[request.form.get('ht_b3_mat', '40X')]
                b3_hard = float(request.form.get('ht_b3_hard_val', 230))
                b3_opt_idx = int(request.form.get('ht_b3_opt', 0))
                sch3 = b3_mat['options'][b3_opt_idx]['sch']

                b3_sh_0, b3_sf_0, sh3_sf, sf3_sf = calc_ht_stress(request.form.get('ht_b3_stress', 'f1'), b3_hard)
                HB3 = b3_hard if b3_mat['type'] == 'HB' else hrc_to_hb(b3_hard)

                NHO1 = 30 * (HB1 ** 2.4)
                N_H1 = 60 * c * Lh * n0 * e
                N_H2 = N_H1 / (u12 * c)
                
                K_HL1 = 1.0 if N_H1 > NHO1 else (NHO1 / N_H1) ** (1/6)
                K_HL2 = 1.0 if N_H2 > NHO1 else (NHO1 / N_H2) ** (1/6)
                    
                sH_cp_12 = min(b1_sh_0 * K_HL1 / sh1_sf, b1_sh_0 * K_HL2 / sh1_sf)
                
                NHO3 = 30 * (HB3 ** 2.4)
                N_H3_val = N_H2 * c / u23
                K_HL3 = 1.0 if N_H3_val > NHO3 else (NHO3 / N_H3_val) ** (1/6)
                    
                sH_cp_3 = b3_sh_0 * K_HL3 / sh3_sf
                
                sF_cp1 = (b1_sf_0 / sf1_sf) * kfc1
                sF_cp2 = (b1_sf_0 / sf1_sf) * kfc2
                sF_cp3 = (b3_sf_0 / sf3_sf) * kfc3

                sH_max1 = 40 * b1_hard if b1_mat['type'] == 'HRC' else 2.8 * sch1
                sF_max1 = 0.6 * sch1 if b1_mat['type'] == 'HRC' else 0.8 * sch1
                sH_max3 = 40 * b3_hard if b3_mat['type'] == 'HRC' else 2.8 * sch3
                sF_max3 = 0.6 * sch3 if b3_mat['type'] == 'HRC' else 0.85 * sch3

                # BƯỚC 3: KÍCH THƯỚC HÌNH HỌC VÀ CHUẨN HÓA AW
                dw1_base = (T1 * KH_Sigma * (u12 + 1)) / ((sH_cp_12**2) * u12 * psiba * c)
                dw1_calc = Kd * math.pow(dw1_base, 1/3)
                
                bw12_calc = psiba * dw1_calc
                bw12 = round(bw12_calc)
                if bw12 % 2 != 0: bw12 += 1
                    
                m_calc = bw12 / 14
                m = get_standard_module(m_calc)
                
                aw_calc = 0.5 * dw1_calc * (u12 + 1)
                aw = get_standard_aw(aw_calc) 
                
                z1 = round((2 * aw / m) / (u12 + 1))
                z2 = round(u12 * z1)
                dw1 = 2 * aw / (u12 + 1)
                dw2 = u12 * dw1

                z3 = round(z1 * e)
                matched = False
                for offset in [0, 1, -1, 2, -2, 3, -3, 4, -4]:
                    if (z1 + (z3 + offset)) % c == 0:
                        z3 = z3 + offset
                        matched = True
                        break
                        
                if not matched: raise Exception("Không tìm được hệ số Z3 thỏa ĐK đồng trục.")

                alpha_t = math.radians(20)
                cos_atw3 = (z3 - z2) / (z1 + z2) * math.cos(alpha_t)
                
                if cos_atw3 >= 1.0 or cos_atw3 <= -1.0:
                    raise Exception("Cấu hình Z1, Z2, Z3 vi phạm định luật ăn khớp. Hãy thử đổi Tỉ số truyền hoặc đổi số lượng Vệ tinh.")
                    
                atw3 = math.acos(cos_atw3)
                inv_atw3 = math.tan(atw3) - atw3
                inv_at = math.tan(alpha_t) - alpha_t
                x3 = ((z3 - z2) * (inv_atw3 - inv_at)) / (2 * math.tan(alpha_t))
                
                u23_thuc = z3 / z2
                dw3 = 2 * aw * u23_thuc / (u23_thuc - 1)
                
                bw3 = round(0.14 * dw3) 
                if bw3 < 15: bw3 = bw12

               # BƯỚC 4: KIỂM NGHIỆM BỀN CẶP 1-2 (RĂNG NGOÀI)
                Zeps_12 = 0.9 
                ZH_12 = 1.76  
                v12 = math.pi * dw1 * n1 / 60000
                KHv_12 = 1.05 
                KH_12 = Kc_rang * KHv_12
                
                T1_nhanh = T1 / c 
                
                sH12_thuc = ZM * ZH_12 * Zeps_12 * math.sqrt((2 * T1_nhanh * KH_12 * (u12 + 1)) / (bw12 * u12 * dw1**2))
                
                KF_12 = Kc_rang * 1.37 * KHv_12
                sF1_thuc = (2 * T1_nhanh * KF_12 * (1/1.5) * YF1) / (bw12 * dw1 * m)

                # BƯỚC 5: KIỂM NGHIỆM BỀN CẶP 2-3 (RĂNG TRONG)
                ZH = math.sqrt(2 / math.sin(2 * atw3))
                db2 = m * z2 * math.cos(alpha_t); da2 = m * (z2 + 2); aa2 = math.acos(db2 / da2)
                db3 = m * z3 * math.cos(alpha_t); da3 = m * (z3 - 2 + 2*x3); aa3 = math.acos(db3 / da3)
                eps_alpha = (z2 * math.tan(aa2) - z3 * math.tan(aa3) + (z3 - z2) * math.tan(atw3)) / (2 * math.pi)
                Zeps = math.sqrt((4 - eps_alpha) / 3) if eps_alpha < 4 else 0.9
                
                n2_n0_quanh_truc = 2 * e * n0 / (e - 1)
                v2o = math.pi * dw2 * n2_n0_quanh_truc / 60000
                
                vH = 0.004 * 73 * v2o * math.sqrt(aw / u23_thuc)
                KHv = 1 + vH * bw3 * dw2 / (2 * T2 * 1.0 * 1.0)
                KH = Kc_rang * 1.0 * KHv 
                sH3_thuc = ZM * ZH * Zeps * math.sqrt((2 * T2 * KH * (u23_thuc - 1)) / (bw3 * u23_thuc * dw2**2))
                
                KFv = 1 + 0.006 * 73 * v2o * math.sqrt(aw / u23_thuc) * bw3 * dw2 / (2 * T2 * 1.0 * 1.37)
                KF = Kc_rang * 1.37 * KFv
                sF2_thuc = (2 * T2 * KF * (1/eps_alpha) * 1.0 * YF2) / (bw3 * dw2 * m)
                sF3_thuc = sF2_thuc * YF3 / YF2

                # QUÁ TẢI
                sH3_max_thuc = sH3_thuc * math.sqrt(Kqt)
                sF2_max_thuc = sF2_thuc * Kqt

                # BƯỚC 6: CHỌN Ổ LĂN VÀ TÍNH LỰC
                df2_val = m * z2 - 2.5 * m
                H_vanh = 2.5 * m
                D_ngoai_o = df2_val - 2 * H_vanh

                Ft = 2 * T1 / dw1
                Ft_ac = 2 * T2 / dw2
                F_chot = 2 * Ft_ac  
                F_r_to_bearing = (4 * T1 * Kc_o) / (dw1 * c) 
                F_lt = 6.7 * (10**-11) * (dw2**2) * bw12 * (n0**2) * aw * 0.5
                
                Q_tai = V_olan * s_olan * math.sqrt(F_r_to_bearing**2 + F_lt**2)
                C_N = C_kN * 1000
                
                L_trieu = (C_N / Q_tai)**(10/3)
                L_h_tinh = (10**6) * L_trieu / (60 * n2_n0_quanh_truc)

                da1_val = m*(z1+2); da2_val = m*(z2+2); da3_val = m*(z3-2+2*x3)
                df1_val = m*z1 - 2.5*m; df3_val = m*z3 + 2.5*m

                check_sH12 = "ĐẠT" if sH12_thuc <= sH_cp_12 else "KHÔNG ĐẠT"
                check_sF1 = "ĐẠT" if sF1_thuc <= sF_cp1 else "KHÔNG ĐẠT"
                check_sH3 = "ĐẠT" if sH3_thuc <= sH_cp_3 else "KHÔNG ĐẠT"
                check_sF2 = "ĐẠT" if sF2_thuc <= sF_cp1 else "KHÔNG ĐẠT"
                check_sF3 = "ĐẠT" if sF3_thuc <= sF_cp2 else "KHÔNG ĐẠT"

                d1 = m * z1
                d2 = m * z2
                d3 = m * z3

                img_b64 = draw_planetary_schematic(d1, d2, aw, c, z1, z2, z3)
                img_html = f'<div style="text-align:center; margin:20px 0;"><img src="data:image/png;base64,{img_b64}" style="max-width:100%; border:1px solid #cbd5e1; border-radius:8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);"></div>'

                result_html = f"""
                <div class="ht-theme">
                <h2 style="text-align:center; color:#1e40af; font-weight:900; margin-top:40px;">BÁO CÁO THIẾT KẾ </h2>
                {img_html}
                <table>
                    <tr><td colspan="3" class="step-title">BƯỚC 1: ĐỘNG HỌC & ĐỒNG TRỤC</td></tr>
                    <tr><th>Tỉ số truyền chung (u10)</th><td><b>{u10:.3f}</b></td><td>= n1 / n0</td></tr>
                    <tr><th>Thông số đặc trưng (e)</th><td><b>{e:.3f}</b></td><td>e = u10 - 1</td></tr>
                    <tr><th>Tỉ số truyền nhánh u12 / u23</th><td><b>{u12:.3f} / {u23_thuc:.3f}</b></td><td>u12 = 0.5(e-1), u23 = z3/z2</td></tr>
                    <tr><th>Mômen Trục ra To</th><td><b>{To:,.0f} N.mm</b></td><td>9.55 * 10^6 * Po / no</td></tr>
                    <tr><th>Mômen M.Trời / V.Tinh (T1/T2)</th><td><b>{T1:,.0f} / {T2:,.0f} N.mm</b></td><td>T1 = To/(e+1) ; T2 = T1.u12/c</td></tr>

                    <tr><td colspan="3" class="step-title">BƯỚC 2: VẬT LIỆU VÀ ỨNG SUẤT CHO PHÉP</td></tr>
                    <tr><th>Số chu kỳ NHO (B1 / B3)</th><td>{NHO1:.2e} / {NHO3:.2e}</td><td>30 * HB^2.4</td></tr>
                    <tr><th>Số chu kỳ tương đương NH (B1/B2/B3)</th><td>{N_H1:.2e} / {N_H2:.2e} / {N_H3_val:.2e}</td><td>Từ Lh, n0, c</td></tr>
                    <tr><th>[σH] Cặp 1-2 / Cặp 2-3</th><td><b style="color:#d97706; font-size:1.1em;">{sH_cp_12:.1f} / {sH_cp_3:.1f} MPa</b></td><td>Đã nhân KHL</td></tr>
                    <tr><th>[σF] B1 / B2 / B3</th><td><b style="color:#d97706; font-size:1.1em;">{sF_cp1:.1f} / {sF_cp1:.1f} / {sF_cp3:.1f} MPa</b></td><td>Đã xét KFC</td></tr>

                    <tr><td colspan="3" class="step-title">BƯỚC 3: KÍCH THƯỚC HÌNH HỌC VÀ CHUẨN HÓA AW</td></tr>
                    <tr><th>Khoảng cách trục Tính toán</th><td>{aw_calc:.2f} mm</td><td>Tính từ T1, u12...</td></tr>
                    <tr><th>Khoảng cách trục Tiêu Chuẩn aw</th><td><b style="color:#1d4ed8; font-size:1.1em;">{aw} mm</b></td><td>Nâng lên dãy số Bảng 6.14</td></tr>
                    <tr><th>Mô đun m</th><td><b style="color:#1d4ed8; font-size:1.1em;">{m:.1f} mm</b></td><td>Tiêu chuẩn (bảng 6.8)</td></tr>
                    <tr><th>Số răng Z1 / Z2 / Z3</th><td><b style="font-size:1.1em;">{z1} / {z2} / {z3}</b></td><td>Thỏa ĐK Đồng trục (Z1+Z3)/{c}</td></tr>
                    <tr><th>Hệ số dịch chỉnh vành răng (X3)</th><td><b style="color:#b91c1c; font-size:1.1em;">{x3:.3f}</b></td><td>Góc ăn khớp αtw3 = {math.degrees(atw3):.2f}°</td></tr>
                    <tr><th>Đường kính vòng lăn (dw1/dw2/dw3)</th><td>{dw1:.1f} / {dw2:.1f} / {dw3:.1f} mm</td><td></td></tr>
                    <tr><th>Bề rộng vành răng bw12 / bw3</th><td>{bw12} / {bw3} mm</td><td>Theo ψbd = {psiba}</td></tr>

                    <tr><td colspan="3" class="step-title" style="background:#0f766e !important;">BƯỚC 4: KIỂM NGHIỆM BỀN CẶP 1-2 (RĂNG NGOÀI)</td></tr>
                    <tr><th>Ứng suất tiếp xúc (σH12)</th><td><b>{sH12_thuc:.1f} MPa</b></td><td class="{'success' if sH12_thuc<=sH_cp_12 else 'highlight'}">{check_sH12} (≤ {sH_cp_12:.1f})</td></tr>
                    <tr><th>Ứng suất uốn Bánh Mặt trời (σF1)</th><td><b>{sF1_thuc:.1f} MPa</b></td><td class="{'success' if sF1_thuc<=sF_cp1 else 'highlight'}">{check_sF1} (≤ {sF_cp1:.1f})</td></tr>

                    <tr><td colspan="3" class="step-title" style="background:#0f766e !important;">BƯỚC 5: KIỂM NGHIỆM BỀN CẶP 2-3 (RĂNG TRONG)</td></tr>
                    <tr><th>Vận tốc v2o / Tải trọng KH / KF</th><td>{v2o:.2f} m/s | KH={KH:.3f} | KF={KF:.3f}</td><td>KHv = {KHv:.3f}</td></tr>
                    <tr><th>Trùng khớp (εα) / Hệ số Zε / ZH</th><td>εα = {eps_alpha:.3f} | Zε = {Zeps:.3f} | ZH={ZH:.3f}</td><td>Tính theo công thức 6.11</td></tr>
                    <tr><th>Ứng suất tiếp xúc (σH3)</th><td><b>{sH3_thuc:.1f} MPa</b></td><td class="{'success' if sH3_thuc<=sH_cp_3 else 'highlight'}">{check_sH3} (≤ {sH_cp_3:.1f})</td></tr>
                    <tr><th>Ứng suất uốn Vệ tinh (σF2)</th><td><b>{sF2_thuc:.1f} MPa</b></td><td class="{'success' if sF2_thuc<=sF_cp1 else 'highlight'}">{check_sF2} (≤ {sF_cp1:.1f})</td></tr>
                    <tr><th>Ứng suất uốn Răng bao (σF3)</th><td><b>{sF3_thuc:.1f} MPa</b></td><td class="{'success' if sF3_thuc<=sF_cp3 else 'highlight'}">{check_sF3} (≤ {sF_cp3:.1f})</td></tr>
                    
                    <tr><td colspan="3" class="step-title" style="background:#0f766e !important;">KIỂM NGHIỆM QUÁ TẢI (Kqt = {Kqt})</td></tr>
                    <tr><th>Quá tải Tiếp xúc Cặp 2-3 (σHmax)</th><td><b>{sH3_max_thuc:.1f} MPa</b></td><td class="{'success' if sH3_max_thuc<=sH_max3 else 'highlight'}">{"ĐẠT" if sH3_max_thuc<=sH_max3 else "KHÔNG ĐẠT"} (≤ {sH_max3:.1f})</td></tr>
                    <tr><th>Quá tải Uốn Vệ tinh (σF2max)</th><td><b>{sF2_max_thuc:.1f} MPa</b></td><td class="{'success' if sF2_max_thuc<=sF_max1 else 'highlight'}">{"ĐẠT" if sF2_max_thuc<=sF_max1 else "KHÔNG ĐẠT"} (≤ {sF_max1:.1f})</td></tr>

                    <tr><td colspan="3" class="step-title" style="background:#b91c1c !important;">BƯỚC 6: CHỌN Ổ LĂN VÀ KIỂM NGHIỆM LỰC</td></tr>
                    <tr><th>Đường kính ngoài tối đa ổ lăn</th><td>D_max = {D_ngoai_o:.1f} mm</td><td>df2 - 2H (H={H_vanh:.1f}mm)</td></tr>
                    <tr><th>Lực vòng ăn khớp (Ft)</th><td>{Ft_ac:,.0f} N</td><td>Tại 1 điểm ăn khớp Cặp 2-3</td></tr>
                    <tr><th>Tổng lực đè lên CHỐT VỆ TINH</th><td><b style="color:#b91c1c; font-size:1.2em;">{F_chot:,.0f} N</b></td><td>F_chot = 2 × Ft (Tính ổ đũa đỡ)</td></tr>
                    <tr><th>Lực ly tâm Vệ Tinh (Flt)</th><td><b style="color:#1d4ed8; font-size:1.1em;">{F_lt:,.1f} N</b></td><td></td></tr>
                    <tr><th>Tải trọng quy ước Q</th><td><b style="color:#d97706; font-size:1.1em;">{Q_tai:,.0f} N</b></td><td>Q = V.s.√(Fr² + Flt²)</td></tr>
                    <tr><th>Tuổi thọ tính toán (Lh_tính)</th><td><b style="font-size:1.3em;" class="{'success' if L_h_tinh>=Lh else 'highlight'}">{L_h_tinh:,.0f} giờ</b></td><td>(Yêu cầu: ≥ {Lh} giờ)</td></tr>

                    <tr><td colspan="3" class="step-title" style="background:#475569 !important;">7. BẢNG TỔNG KẾT KÍCH THƯỚC BỘ TRUYỀN</td></tr>
                    <tr><th style="background:#f1f5f9;">Thông Số</th><th style="background:#f1f5f9;">Cặp Răng Ngoài 1-2</th><th style="background:#f1f5f9;">Cặp Răng Trong 2-3</th></tr>
                    <tr><th>Đường kính chia d</th><td>d1={d1:.1f} ; d2={d2:.1f}</td><td>d3={d3:.1f}</td></tr>
                    <tr><th>Đường kính đỉnh da</th><td>da1={da1_val:.1f} ; da2={da2_val:.1f}</td><td>da3={da3_val:.2f}</td></tr>
                    <tr><th>Đường kính đáy df</th><td>df1={df1_val:.1f} ; df2={df2_val:.1f}</td><td>df3={df3_val:.2f}</td></tr>
                </table>
                </div>
                """
            except Exception as e:
                trace = traceback.format_exc()
                result_html = f"<div class='error-box'><b>Lỗi tính toán Hành tinh:</b> {str(e)}<br><span style='font-size:12px;color:#9ca3af;'>{trace}</span></div>"

    return render_template_string(HTML_PAGE, 
                                  gen_mat_db_json=json.dumps(GENERAL_MATERIAL_DB), 
                                  gen_mat_db=GENERAL_MATERIAL_DB,
                                  gen_shlim_db_json=json.dumps(SHLIM_FORMULAS), 
                                  gen_sflim_db_json=json.dumps(SFLIM_FORMULAS),
                                  ht_mat_db_json=json.dumps(HT_MATERIAL_DB), 
                                  ht_mat_db=HT_MATERIAL_DB,
                                  ht_stress_db_json=json.dumps(HT_STRESS_DB),
                                  result_html=result_html)

if __name__ == '__main__':
    app.run(debug=True, port=5091)