"""
EduPredict - Generate Flowcharts and DFDs as PNG images
Run: python generate_diagrams.py
Output: diagrams/ folder with all PNG files
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

os.makedirs('diagrams', exist_ok=True)

BG    = '#07071a'
PURP  = '#a855f7'
CYAN  = '#22d3ee'
GREEN = '#22c55e'
RED   = '#ef4444'
ORANGE= '#f97316'
WHITE = '#f1f0ff'
GRAY  = '#6b5f8a'

def box(ax, x, y, w, h, text, color=PURP, fontsize=9, radius=0.04):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                          boxstyle=f"round,pad=0.02,rounding_size={radius}",
                          facecolor=color+'22', edgecolor=color, linewidth=1.8)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=WHITE, fontweight='bold', wrap=True,
            multialignment='center')

def diamond(ax, x, y, w, h, text, color=ORANGE, fontsize=8):
    dx, dy = w/2, h/2
    pts = [(x, y+dy), (x+dx, y), (x, y-dy), (x-dx, y)]
    poly = plt.Polygon(pts, facecolor=color+'22', edgecolor=color, linewidth=1.8)
    ax.add_patch(poly)
    ax.text(x, y, text, ha='center', va='center', fontsize=fontsize,
            color=WHITE, fontweight='bold', multialignment='center')

def arrow(ax, x1, y1, x2, y2, color=GRAY, label=''):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=1.5))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx+0.05, my, label, fontsize=7, color=CYAN)

def setup(title, figsize=(8, 12)):
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')
    ax.set_title(title, color=PURP, fontsize=13, fontweight='bold', pad=12)
    return fig, ax

# ─────────────────────────────────────────────
# DIAGRAM 1: Login / Authentication Flowchart
# ─────────────────────────────────────────────
fig, ax = setup('Flowchart 1: User Authentication & Login')

box(ax, 5, 13,   2.2, 0.6, 'START',           GREEN)
arrow(ax, 5,12.7, 5,12.1)
box(ax, 5, 11.8, 3.2, 0.6, 'User Opens Login Page', PURP)
arrow(ax, 5,11.5, 5,10.9)
box(ax, 5, 10.6, 3.6, 0.6, 'Enter Username, Password, Role', PURP)
arrow(ax, 5,10.3, 5, 9.7)
diamond(ax, 5, 9.3, 3.4, 0.7, 'Credentials\nValid?', ORANGE)
arrow(ax, 5, 8.95, 5, 8.3, label='Yes')
ax.annotate('', xy=(8.2, 9.3), xytext=(6.7, 9.3),
            arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))
ax.text(7.2, 9.45, 'No', fontsize=7, color=RED)
box(ax, 8.8, 9.3, 2.0, 0.6, 'Show Error\nFlash Msg', RED)
arrow(ax, 8.8, 9.0, 8.8, 8.3)
ax.annotate('', xy=(6.5, 8.0), xytext=(8.8, 8.0),
            arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.2))

box(ax, 5, 8.0,  3.4, 0.6, 'Create Session\n(user, role)', CYAN)
arrow(ax, 5, 7.7, 5, 7.1)
box(ax, 5, 6.8,  3.4, 0.6, 'Load Role-Based\nAccess List', PURP)
arrow(ax, 5, 6.5, 5, 5.9)
box(ax, 5, 5.6,  3.0, 0.6, 'Redirect to Dashboard', GREEN)
arrow(ax, 5, 5.3, 5, 4.7)
box(ax, 5, 4.4,  2.2, 0.6, 'END', RED)

plt.tight_layout()
plt.savefig('diagrams/01_login_flowchart.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("[OK] 01_login_flowchart.png")

# ─────────────────────────────────────────────
# DIAGRAM 2: ML Prediction Flowchart
# ─────────────────────────────────────────────
fig, ax = setup('Flowchart 2: ML Prediction Engine')

box(ax, 5, 13,   2.2, 0.6, 'START', GREEN)
arrow(ax, 5,12.7, 5,12.1)
box(ax, 5, 11.8, 3.4, 0.6, 'User Selects Prediction Type', PURP)
arrow(ax, 5,11.5, 5,10.9)
diamond(ax, 5, 10.5, 3.6, 0.7, 'Type?', ORANGE)

# Exam Score branch
ax.annotate('', xy=(2.0, 10.5), xytext=(3.2, 10.5),
            arrowprops=dict(arrowstyle='->', color=CYAN, lw=1.5))
ax.text(2.2, 10.65, 'Exam', fontsize=7, color=CYAN)
box(ax, 1.5, 9.5, 2.4, 0.6, 'Enter 21\nStudent Features', CYAN)
arrow(ax, 1.5, 9.2, 1.5, 8.5)
box(ax, 1.5, 8.2, 2.4, 0.6, 'Scale Features\n(StandardScaler)', PURP)
arrow(ax, 1.5, 7.9, 1.5, 7.2)
box(ax, 1.5, 6.9, 2.4, 0.6, 'RF Regressor\nPredict Score', PURP)
arrow(ax, 1.5, 6.6, 1.5, 5.9)
box(ax, 1.5, 5.6, 2.4, 0.6, 'Show Score +\nAlert Level', GREEN)

# Dropout branch
ax.annotate('', xy=(5.0, 9.8), xytext=(5.0, 10.15),
            arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))
ax.text(5.1, 10.0, 'Dropout', fontsize=7, color=RED)
box(ax, 5, 9.5, 2.4, 0.6, 'Enter Student\nFeatures', RED)
arrow(ax, 5, 9.2, 5, 8.5)
box(ax, 5, 8.2, 2.4, 0.6, 'RF Classifier\nPredict Risk', PURP)
arrow(ax, 5, 7.9, 5, 7.2)
box(ax, 5, 6.9, 2.4, 0.6, 'Show Risk %\n+ Alert', RED)
arrow(ax, 5, 6.6, 5, 5.9)
box(ax, 5, 5.6, 2.4, 0.6, 'Trigger Alert\nif Critical', ORANGE)

# Course branch
ax.annotate('', xy=(8.5, 10.5), xytext=(6.8, 10.5),
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5))
ax.text(7.3, 10.65, 'Course', fontsize=7, color=GREEN)
box(ax, 8.8, 9.5, 2.2, 0.6, 'Enter Enrollment\n& Category', GREEN)
arrow(ax, 8.8, 9.2, 8.8, 8.5)
box(ax, 8.8, 8.2, 2.2, 0.6, 'Apply Growth\nFormula', PURP)
arrow(ax, 8.8, 7.9, 8.8, 7.2)
box(ax, 8.8, 6.9, 2.2, 0.6, 'Show Forecast\n+ Trend', GREEN)

# Merge
arrow(ax, 1.5, 5.3, 1.5, 4.5)
arrow(ax, 5,   5.3, 5,   4.5)
arrow(ax, 8.8, 6.6, 8.8, 4.5)
box(ax, 5, 4.2, 3.0, 0.6, 'Display Results\nto User', CYAN)
arrow(ax, 5, 3.9, 5, 3.3)
box(ax, 5, 3.0, 2.2, 0.6, 'END', RED)

plt.tight_layout()
plt.savefig('diagrams/02_prediction_flowchart.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("[OK] 02_prediction_flowchart.png")

# ─────────────────────────────────────────────
# DIAGRAM 3: Data Ingestion Flowchart
# ─────────────────────────────────────────────
fig, ax = setup('Flowchart 3: Data Ingestion Pipeline')

box(ax, 5, 13,   2.2, 0.6, 'START', GREEN)
arrow(ax, 5,12.7, 5,12.1)
box(ax, 5, 11.8, 3.6, 0.6, 'Admin/Analyst Selects\nDataset Type', PURP)
arrow(ax, 5,11.5, 5,10.9)
diamond(ax, 5, 10.5, 3.4, 0.7, 'Source Type?', ORANGE)

ax.annotate('', xy=(2.0,10.5), xytext=(3.3,10.5),
            arrowprops=dict(arrowstyle='->', color=CYAN, lw=1.5))
ax.text(1.8,10.65,'Batch',fontsize=7,color=CYAN)
box(ax, 1.5, 9.5, 2.4, 0.6, 'Upload CSV/\nParquet File', CYAN)

ax.annotate('', xy=(8.5,10.5), xytext=(6.7,10.5),
            arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.5))
ax.text(7.3,10.65,'Stream',fontsize=7,color=GREEN)
box(ax, 8.8, 9.5, 2.2, 0.6, 'Kafka Stream\nConnector', GREEN)

arrow(ax, 1.5, 9.2, 1.5, 8.5)
arrow(ax, 8.8, 9.2, 8.8, 8.5)
box(ax, 1.5, 8.2, 2.4, 0.6, 'Validate\nData Format', PURP)
box(ax, 8.8, 8.2, 2.2, 0.6, 'Buffer &\nValidate', PURP)

arrow(ax, 1.5, 7.9, 1.5, 7.2)
arrow(ax, 8.8, 7.9, 8.8, 7.2)
diamond(ax, 1.5, 6.8, 2.4, 0.7, 'Valid?', ORANGE)
diamond(ax, 8.8, 6.8, 2.4, 0.7, 'Valid?', ORANGE)

arrow(ax, 1.5, 6.45, 1.5, 5.8, label='Yes')
arrow(ax, 8.8, 6.45, 8.8, 5.8, label='Yes')
ax.text(0.5, 6.8, 'No→Log\nError', fontsize=7, color=RED)
ax.text(9.6, 6.8, 'No→\nDiscard', fontsize=7, color=RED)

box(ax, 1.5, 5.5, 2.4, 0.6, 'Write to\nHDFS', CYAN)
box(ax, 8.8, 5.5, 2.2, 0.6, 'Write to\nHDFS', CYAN)

arrow(ax, 1.5, 5.2, 1.5, 4.5)
arrow(ax, 8.8, 5.2, 8.8, 4.5)
box(ax, 5, 4.2, 3.4, 0.6, 'Update Ingestion Log\n+ Flash Success', GREEN)
arrow(ax, 5, 3.9, 5, 3.3)
box(ax, 5, 3.0, 2.2, 0.6, 'END', RED)

plt.tight_layout()
plt.savefig('diagrams/03_ingestion_flowchart.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("[OK] 03_ingestion_flowchart.png")

# ─────────────────────────────────────────────
# DIAGRAM 4: Level-0 DFD (Context Diagram)
# ─────────────────────────────────────────────
fig, ax = setup('DFD Level-0: Context Diagram — EduPredict System', figsize=(10, 8))
ax.set_xlim(0, 12)
ax.set_ylim(0, 10)

# Central system
box(ax, 6, 5, 3.0, 1.2, 'EduPredict\nSystem', PURP, fontsize=11)

# External entities
box(ax, 1.5, 8.5, 2.2, 0.8, 'Administrator', CYAN, fontsize=9)
box(ax, 1.5, 5.0, 2.2, 0.8, 'Teacher', GREEN, fontsize=9)
box(ax, 1.5, 1.5, 2.2, 0.8, 'Student', ORANGE, fontsize=9)
box(ax, 10.5, 8.5, 2.2, 0.8, 'Analyst', CYAN, fontsize=9)
box(ax, 10.5, 1.5, 2.2, 0.8, 'Data Sources\n(CSV/Stream)', RED, fontsize=8)

# Arrows
arrow(ax, 2.6, 8.5, 4.5, 5.8, CYAN, 'Manage Users\nIngestion')
arrow(ax, 4.5, 5.4, 2.6, 5.0, GREEN, 'Alerts\nReports')
arrow(ax, 2.6, 5.0, 4.5, 5.2, GREEN, 'View Predictions')
arrow(ax, 2.6, 1.5, 4.5, 4.5, ORANGE, 'Student Input')
arrow(ax, 7.5, 5.5, 9.4, 8.5, CYAN, 'Analytics\nDashboard')
arrow(ax, 9.4, 8.2, 7.5, 5.8, CYAN, 'Data Queries')
arrow(ax, 9.4, 1.5, 7.5, 4.5, RED, 'Raw Data\nIngestion')

plt.tight_layout()
plt.savefig('diagrams/04_dfd_level0.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("[OK] 04_dfd_level0.png")

# ─────────────────────────────────────────────
# DIAGRAM 5: Level-1 DFD
# ─────────────────────────────────────────────
fig, ax = setup('DFD Level-1: EduPredict Sub-Processes', figsize=(12, 10))
ax.set_xlim(0, 14)
ax.set_ylim(0, 12)

# Processes
box(ax, 3,  10.5, 2.8, 0.8, 'P1: User Auth\n& RBAC',       PURP, fontsize=9)
box(ax, 9,  10.5, 2.8, 0.8, 'P2: Data\nIngestion',         CYAN, fontsize=9)
box(ax, 3,  7.0,  2.8, 0.8, 'P3: ML\nPrediction Engine',   PURP, fontsize=9)
box(ax, 9,  7.0,  2.8, 0.8, 'P4: Real-Time\nProcessing',   GREEN, fontsize=9)
box(ax, 3,  3.5,  2.8, 0.8, 'P5: Alerts &\nNotifications', RED, fontsize=9)
box(ax, 9,  3.5,  2.8, 0.8, 'P6: Reports &\nDashboard',    ORANGE, fontsize=9)

# Data Stores
box(ax, 6,  8.5,  2.4, 0.6, 'DS1: HDFS\nStorage',          GRAY, fontsize=8)
box(ax, 6,  5.5,  2.4, 0.6, 'DS2: ML\nModels (.pkl)',       GRAY, fontsize=8)
box(ax, 6,  2.5,  2.4, 0.6, 'DS3: User\nSession Store',     GRAY, fontsize=8)

# External
box(ax, 0.8, 7.0, 1.8, 0.7, 'Users', CYAN, fontsize=8)
box(ax, 12.5,7.0, 1.8, 0.7, 'Data\nSources', RED, fontsize=8)

# Arrows
arrow(ax, 1.7, 7.0, 1.6, 10.5, CYAN)
arrow(ax, 4.4, 10.5, 5.0, 8.5, PURP, 'Auth OK')
arrow(ax, 7.0, 8.5, 7.6, 10.5, CYAN, 'Store')
arrow(ax, 11.8,7.0, 10.4,10.5, RED, 'Raw Data')
arrow(ax, 7.6, 8.2, 7.0, 5.5, GRAY, 'Load Data')
arrow(ax, 5.0, 5.5, 4.4, 7.0, PURP, 'Predict')
arrow(ax, 4.4, 7.0, 5.0, 5.5, PURP)
arrow(ax, 7.6, 7.0, 10.4,7.0, GREEN, 'Stream')
arrow(ax, 4.4, 3.5, 5.0, 2.5, RED, 'Session')
arrow(ax, 7.0, 2.5, 7.6, 3.5, ORANGE)
arrow(ax, 4.4, 7.2, 4.4, 3.9, RED, 'Trigger Alert')
arrow(ax, 7.6, 7.2, 7.6, 3.9, ORANGE, 'Feed Report')
arrow(ax, 1.7, 7.2, 1.7, 3.5, CYAN)
arrow(ax, 12.2,7.2, 10.4,3.5, ORANGE)

plt.tight_layout()
plt.savefig('diagrams/05_dfd_level1.png', dpi=150, bbox_inches='tight', facecolor=BG)
plt.close()
print("[OK] 05_dfd_level1.png")

print("\nAll diagrams saved in: diagrams/")
print("Files: 01_login_flowchart.png, 02_prediction_flowchart.png,")
print("       03_ingestion_flowchart.png, 04_dfd_level0.png, 05_dfd_level1.png")
