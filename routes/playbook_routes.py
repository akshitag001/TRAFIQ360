from flask import Blueprint, request, jsonify, send_file, send_from_directory
import os
import uuid
import time
import folium
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from core.config import playbooks_dir

playbook_bp = Blueprint('playbook', __name__)

def capture_map_screenshot(blocked_corridor, blocked_coords, alt_route_coords):
    map_html_path = os.path.join(playbooks_dir, f"temp_map_{uuid.uuid4().hex}.html")
    map_png_path = os.path.join(playbooks_dir, f"map_screenshot_{uuid.uuid4().hex}.png")
    
    try:
        # Determine center
        if blocked_coords and len(blocked_coords) > 0:
            center_lat = sum([c[1] for c in blocked_coords]) / len(blocked_coords)
            center_lon = sum([c[0] for c in blocked_coords]) / len(blocked_coords)
        elif alt_route_coords and len(alt_route_coords) > 0:
            center_lat = sum([c[1] for c in alt_route_coords]) / len(alt_route_coords)
            center_lon = sum([c[0] for c in alt_route_coords]) / len(alt_route_coords)
        else:
            center_lat, center_lon = 12.9716, 77.5946

        m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles='cartodbpositron')

        # Add blocked segment
        if blocked_coords:
            b_path = [[c[1], c[0]] for c in blocked_coords]
            folium.PolyLine(b_path, color='red', weight=6, dash_array='10, 5', opacity=0.8, popup=f"BLOCKED: {blocked_corridor}").addTo(m)

        # Add alt route
        if alt_route_coords:
            a_path = [[c[1], c[0]] for c in alt_route_coords]
            folium.PolyLine(a_path, color='green', weight=5, opacity=0.8, popup="RECOMMENDED DIVERSION").addTo(m)

        m.save(map_html_path)

        # Selenium headless screenshot
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=800,600")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(f"file:///{os.path.abspath(map_html_path)}")
        time.sleep(2) # Wait for tiles to load
        driver.save_screenshot(map_png_path)
        driver.quit()
        
        return map_png_path
    except Exception as e:
        print(f"Error capturing map screenshot: {e}")
        return None
    finally:
        if os.path.exists(map_html_path):
            try:
                os.remove(map_html_path)
            except:
                pass

@playbook_bp.route('/playbooks/<path:filename>', methods=['GET'])
def serve_playbook(filename):
    try:
        return send_file(os.path.join(playbooks_dir, filename))
    except Exception as e:
        print(f"[ERROR] /playbooks/<path> failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@playbook_bp.route('/download/playbook/<path:filename>', methods=['GET'])
def download_playbook(filename):
    try:
        return send_from_directory(playbooks_dir, filename, as_attachment=True)
    except Exception as e:
        print(f"[ERROR] /download/playbook failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

@playbook_bp.route('/api/generate-playbook', methods=['POST'])
def generate_playbook():
    try:
        data = request.json or {}
        pred = data.get('prediction', {})
        opt = data.get('optimization', {})
        div = data.get('diversion', {})

        event_cause = pred.get('event_cause', 'Unknown')
        corridor = pred.get('corridor', 'Unknown')
        impact_score = float(pred.get('impact_score', 5.0))
        closure_prob = float(pred.get('closure_probability', 0.5))
        expected_duration = float(pred.get('expected_duration', 1.0))
        priority = pred.get('priority', 'Medium')

        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_cause = str(event_cause).replace(' ', '_').replace('/', '-')
        safe_corridor = str(corridor).replace(' ', '_').replace('/', '-')
        filename = f"playbook_{safe_cause}_{safe_corridor}_{timestamp_str}.pdf"
        filepath = os.path.join(playbooks_dir, filename)

        map_png_path = None
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, spaceAfter=20, alignment=1)
            h2_style = ParagraphStyle('H2Style', parent=styles['Heading2'], fontSize=16, spaceAfter=12, spaceBefore=16, textColor=colors.HexColor('#1f2937'))
            normal_style = styles['Normal']

            story = []

            # PAGE 1: COVER
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph("<b>TRAFIQ360 Operational Playbook</b>", title_style))
            story.append(Spacer(1, 0.5*inch))

            data_details = [
                ['Cause', event_cause.replace('_', ' ').title()],
                ['Corridor', corridor],
                ['Date', datetime.now().strftime('%Y-%m-%d')],
                ['Hour', str(pred.get('hour', 'N/A'))],
                ['Priority', priority]
            ]
            t = Table(data_details, colWidths=[2*inch, 3*inch])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#111827')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,-1), 8),
                ('TOPPADDING', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
            ]))
            story.append(t)
            story.append(Spacer(1, 0.5*inch))

            if impact_score >= 7:
                bg_color, text_color = '#fee2e2', '#b91c1c'
            elif impact_score >= 5:
                bg_color, text_color = '#fef3c7', '#b45309'
            else:
                bg_color, text_color = '#d1fae5', '#047857'

            badge_data = [[f"IMPACT SCORE: {impact_score:.1f} / 10.0"]]
            t_badge = Table(badge_data, colWidths=[5*inch])
            t_badge.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
                ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor(text_color)),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 16),
                ('BOTTOMPADDING', (0,0), (-1,-1), 12),
                ('TOPPADDING', (0,0), (-1,-1), 12),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor(text_color)),
            ]))
            story.append(t_badge)
            story.append(Spacer(1, 2*inch))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ParagraphStyle('Footer', parent=normal_style, alignment=1, textColor=colors.gray)))
            story.append(Paragraph("<b>BENGALURU TRAFFIC POLICE - CONFIDENTIAL</b>", ParagraphStyle('FooterBold', parent=normal_style, alignment=1, textColor=colors.gray)))
            story.append(PageBreak())

            # PAGE 2: PREDICTION
            story.append(Paragraph("ML Prediction Summary", h2_style))
            story.append(Paragraph(f"<b>Closure Probability:</b> {closure_prob*100:.1f}%", normal_style))
            duration_h = int(expected_duration)
            duration_m = int((expected_duration - duration_h) * 60)
            story.append(Paragraph(f"<b>Expected Duration:</b> {duration_h}h {duration_m}m", normal_style))
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph("<b>Prediction Drivers (SHAP)</b>", normal_style))
            story.append(Spacer(1, 0.1*inch))
            drivers = pred.get('impact_drivers', [])
            if drivers:
                sh_data = [['Feature', 'Contribution', 'Direction']]
                for d in drivers:
                    sh_data.append([str(d.get('feature', '')), f"{d.get('value', 0):.3f}", str(d.get('direction', ''))])
                t_shap = Table(sh_data, colWidths=[2.5*inch, 1.5*inch, 1*inch])
                t_shap.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#374151')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
                ]))
                story.append(t_shap)
            else:
                story.append(Paragraph("No driver data available.", normal_style))
            story.append(PageBreak())

            # PAGE 3: RESOURCES
            story.append(Paragraph("Resource Deployment Plan", h2_style))
            alloc = opt.get('allocations', [])
            if alloc:
                res_data = [['Junction', 'Officers', 'Barricades', 'Priority']]
                tot_off, tot_bar = 0, 0
                for a in alloc:
                    off = a.get('officers', 0)
                    bar = a.get('barricades', 0)
                    tot_off += off
                    tot_bar += bar
                    res_data.append([a.get('junction', 'Unknown'), str(off), str(bar), "HIGH" if off > 3 else "MEDIUM"])
                t_res = Table(res_data, colWidths=[2.5*inch, 1*inch, 1*inch, 1*inch])
                t_res.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1d4ed8')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
                ]))
                story.append(t_res)
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph(f"<b>Total:</b> {tot_off} Officers | {tot_bar} Barricades", ParagraphStyle('B', parent=normal_style, fontSize=12)))
            story.append(Spacer(1, 0.3*inch))
            story.append(Paragraph("<b>Escalation Contacts</b>", normal_style))
            story.append(Paragraph("DCP Traffic East: +91-9876543210", normal_style))
            story.append(Paragraph("ACP Control Room: +91-8765432109", normal_style))
            story.append(PageBreak())

            # PAGE 4: DIVERSIONS
            story.append(Paragraph("Diversion Routes", h2_style))
            alt_routes = div.get('alternate_routes', [])
            blocked_seg = div.get('blocked_segment', {})
            if alt_routes:
                story.append(Paragraph(f"<b>Blocked Segment:</b> {blocked_seg.get('corridor', 'Unknown')}", normal_style))
                story.append(Spacer(1, 0.2*inch))
                div_data = [['Rank', 'Via Corridors', 'Distance', 'Secondary Load', 'Status']]
                for r in alt_routes:
                    div_data.append([
                        str(r.get('rank', '-')),
                        ", ".join(r.get('passes_through', [])),
                        f"{r.get('distance_m', 0)/1000:.1f} km",
                        f"{r.get('secondary_load_pct', 0):.1f}%",
                        r.get('recommendation', '')
                    ])
                t_div = Table(div_data, colWidths=[0.5*inch, 2*inch, 1*inch, 1.2*inch, 1*inch])
                t_div.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#047857')),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e5e7eb')),
                ]))
                story.append(t_div)
            else:
                story.append(Paragraph("No alternate routes calculated.", normal_style))
            story.append(PageBreak())

            # PAGE 5: MAP
            story.append(Paragraph("Geospatial Overview", h2_style))
            blocked_coords = blocked_seg.get('geojson', {}).get('coordinates', []) if blocked_seg else []
            alt_coords = alt_routes[0].get('geojson', {}).get('coordinates', []) if alt_routes else []
            map_png_path = capture_map_screenshot(blocked_seg.get('corridor', 'Unknown'), blocked_coords, alt_coords)
            if map_png_path and os.path.exists(map_png_path):
                story.append(RLImage(map_png_path, width=6*inch, height=4.5*inch))
                story.append(Spacer(1, 0.2*inch))
                story.append(Paragraph("Red: Blocked | Green: Recommended Diversion", ParagraphStyle('Cap', parent=normal_style, alignment=1, fontSize=9, textColor=colors.gray)))
            else:
                story.append(Paragraph("<i>[Map visualization unavailable]</i>", normal_style))

            doc.build(story)

        except Exception as pdf_err:
            print(f"[WARN] Full PDF generation failed: {pdf_err}. Using minimal fallback.")
            try:
                _doc = SimpleDocTemplate(filepath, pagesize=letter)
                _styles = getSampleStyleSheet()
                _story = [
                    Paragraph("TRAFIQ360 Operational Playbook", _styles['Heading1']),
                    Paragraph(f"Event: {event_cause} | Corridor: {corridor}", _styles['Normal']),
                    Paragraph(f"Impact Score: {impact_score:.1f}/10 | Closure Prob: {closure_prob*100:.0f}%", _styles['Normal']),
                    Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", _styles['Normal']),
                    Paragraph("BENGALURU TRAFFIC POLICE - CONFIDENTIAL", _styles['Normal']),
                ]
                _doc.build(_story)
            except Exception as fallback_err:
                print(f"[ERROR] Minimal PDF also failed: {fallback_err}")
                return jsonify({'success': False, 'error': str(fallback_err)}), 500

        # Cleanup map image
        try:
            if map_png_path and os.path.exists(map_png_path):
                os.remove(map_png_path)
        except Exception:
            pass

        return jsonify({
            'success': True,
            'download_url': f'/download/playbook/{filename}',
            'filename': filename
        })
    except Exception as e:
        print(f"[ERROR] /api/generate-playbook failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500
