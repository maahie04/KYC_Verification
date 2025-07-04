"""Generates a downloadable report which tells the user about the status of verification of each step."""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import datetime
from io import BytesIO
import streamlit as st
import base64
from PIL import Image as PILImage
import numpy as np
from profile_utils import get_user_profile
from supabase_client import supabase
def create_verification_pdf_reportlab():
    """Generate a comprehensive PDF verification report"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30)
        
        styles = getSampleStyleSheet()
        
        if 'Title' not in styles:
            styles.add(ParagraphStyle(
                name='Title', 
                fontSize=16, 
                alignment=1, 
                spaceAfter=12,
                fontName='Helvetica-Bold'
            ))
        
        if 'Header' not in styles:
            styles.add(ParagraphStyle(
                name='Header', 
                fontSize=12, 
                spaceAfter=6,
                fontName='Helvetica-Bold'
            ))
        
        if 'Body' not in styles:
            styles.add(ParagraphStyle(
                name='Body', 
                fontSize=10, 
                spaceAfter=6,
                fontName='Helvetica'
            ))
        
        if 'Footer' not in styles:
            styles.add(ParagraphStyle(
                name='Footer',
                fontSize=8,
                alignment=1,
                fontName='Helvetica-Oblique'
            ))
        
        story = []
        
        story.append(Paragraph("IDENTITY VERIFICATION REPORT", styles['Title']))
        story.append(Paragraph(
            f"Generated on: {datetime.datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}", 
            styles['Body']
        ))
        story.append(Spacer(1, 0.3*inch))
        user_profile=get_user_profile(st.session_state.get("user_email"))
        story.append(Paragraph("USER INFORMATION", styles['Header']))
        user_data = [
            ["User ID:", str(user_profile.get('id', 'N/A'))],
            ["Full Name:", str(user_profile.get('name', 'Not provided'))],
            ["Email Address:", st.session_state.get('user_email', 'Not provided')],
            ["Verification Date:", datetime.datetime.now().strftime('%Y-%m-%d')]
        ]
        
        user_table = Table(user_data, colWidths=[1.8*inch, 4.2*inch])
        user_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        story.append(user_table)
        story.append(Spacer(1, 0.3*inch))
        
        if st.session_state.get('extracted_data'):
            story.append(Paragraph("DOCUMENT DETAILS", styles['Header']))
            
            doc_data = []
            for doc_type, data in st.session_state.extracted_data.items():
                doc_info = data.get('document_data', {})
                expiry_info = data.get('expiry_info', {})
                
                doc_data.append(["Document Type:", doc_type.capitalize() if doc_type else "N/A"])
                doc_data.append(["Document Number:", doc_info.get('document_number', 'N/A')])
                doc_data.append(["Name on Document:", doc_info.get('name', 'N/A')])
                doc_data.append(["Date of Birth:", doc_info.get('dob', 'N/A')])
                doc_data.append(["Expiry Date:", expiry_info.get('expiry_date', 'N/A')])
                doc_data.append(["Status:", "VALID" if expiry_info.get('is_valid', True) else "EXPIRED/INVALID"])
                doc_data.append(["", ""])  
            
            if doc_data:
                doc_data.pop()  
                docs_table = Table(doc_data, colWidths=[1.8*inch, 4.2*inch])
                docs_table.setStyle(TableStyle([
                    ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
                    ('FONTSIZE', (0,0), (-1,-1), 10),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey)
                ]))
                story.append(docs_table)
                story.append(Spacer(1, 0.3*inch))
        
        story.append(Paragraph("VERIFICATION STATUS", styles['Header']))
        
        verification_data = []
        verification_steps = [
            ("Profile Information", st.session_state.get('profile_complete', False)),
            ("Document Verification", st.session_state.get('verified', False)),
            ("Live Verification", st.session_state.get('live_verified', False)),
            ("Signature Upload", st.session_state.get('signature_uploaded', False))
        ]
        
        for step, completed in verification_steps:
            status = "COMPLETED" if completed else "PENDING"
            verification_data.append([step, status])
        
        verification_table = Table(
            verification_data, 
            colWidths=[3.5*inch, 1.5*inch],
            hAlign='LEFT'
        )
        verification_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,-1), 'CENTER'),
            ('TEXTCOLOR', (1,0), (1,-1), colors.black),
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
            ('BOX', (0,0), (-1,-1), 0.5, colors.black)
        ]))
        story.append(verification_table)
        story.append(Spacer(1, 0.3*inch))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            "This document serves as proof of identity verification. "
            "For any inquiries, please contact support@yourdomain.com",
            styles['Footer']
        ))
        
        doc.build(story)
        pdf_data = buffer.getvalue()
        buffer.close()
        return pdf_data
        
    except Exception as e:
        st.error(f"Failed to generate PDF: {str(e)}")
        return None
def update_verification_status_in_db():
    """Update the user_verification table with verification status"""
    try:
        user_email = st.session_state.get("user_email")
        if not user_email:
            st.error("No user email found in session")
            return False

        user_profile = get_user_profile(user_email)
        if not user_profile:
            st.error("Could not retrieve user profile")
            return False

        user_id = user_profile.get('id')
        user_name = user_profile.get('name')
        
        verification_data = {
            "id": user_id,
            "email": user_email,
            "name": user_name,
            "profile_uploaded": st.session_state.get('profile_complete', False),
            "documents_uploaded": st.session_state.get('verified', False),
            "documents_verified": st.session_state.get('verified', False),
            "live_verification": st.session_state.get('live_verified', False),
            "signature_uploaded": st.session_state.get('signature_uploaded', False)
        }

        if all(verification_data.values()):
            verification_data["verified_at"] = datetime.datetime.now().isoformat()

        response = supabase.table("user_verification").upsert(
            verification_data,
            on_conflict="id" 
        ).execute()

        if response.data:
            print(f"Successfully updated verification status for {user_email}")
            return True
        else:
            st.error("Failed to update verification status - no data returned")
            return False

    except Exception as e:
        st.error(f"Error updating verification status: {str(e)}")
        print(f"Error details: {str(e)}")
        return False
    
def verification_report_page():
    
    required_steps = {
        'Profile Information': st.session_state.get('profile_complete', False),
        'Document Verification': st.session_state.get('verified', False),
        'Live Verification': st.session_state.get('live_verified', False),
        'Signature Upload': st.session_state.get('signature_uploaded', False)
    }
    
    all_complete = all(required_steps.values())
    
    st.title("Verification Report")
    
    if all_complete:
        st.success("🎉 Your identity verification is complete!")
    else:
        missing = [step for step, completed in required_steps.items() if not completed]
        st.warning(f"⚠️ Verification not yet complete. Missing steps: {', '.join(missing)}")
    
    
    with st.spinner("Generating your verification report..."):
        pdf_data = create_verification_pdf_reportlab()
        update_verification_status_in_db() 
    
    if not pdf_data:
        st.error("Failed to generate the verification report. Please try again.")
        return

    st.subheader("Verification Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Profile Information")
        st.write(f"**Name:** {st.session_state.get('user_name', 'Not provided')}")
        st.write(f"**Email:** {st.session_state.get('user_email', 'Not provided')}")
        st.write(f"**Phone:** {st.session_state.get('user_phone', 'Not provided')}")
    
    with col2:
        st.markdown("### Document Details")
        if st.session_state.get('extracted_data'):
            for doc_type, data in st.session_state.extracted_data.items():
                doc_data = data.get('document_data', {})
                expiry_info = data.get('expiry_info', {})
                
                st.write(f"**Document Type:** {doc_type}")
                st.write(f"**Document Number:** {doc_data.get('document_number', 'N/A')}")
                st.write(f"**Expiry Status:** {'Valid' if expiry_info.get('is_valid', True) else 'Expired/Invalid'}")
        else:
            st.warning("No document data available")
    
    st.markdown("---")
    st.markdown("### Verification Steps")
    
    for step, completed in required_steps.items():
        status = "✅ Completed" if completed else "❌ Pending"
        st.markdown(f"- {step}: {status}")

    st.markdown("---")
    st.subheader("Download Your Report")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.download_button(
            label="📄 Download PDF Report",
            data=pdf_data,
            file_name=f"verification_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            mime="application/pdf",
            help="Download a PDF copy of your verification report",
            key="pdf_download"
        )
    
    with col2:
        if st.button("🔄 Return to Dashboard"):
            st.session_state.current_page = "Profile Details"
            st.rerun()
