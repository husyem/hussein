import streamlit as st
import os
import tempfile
import io
import google.generativeai as genai
from PIL import Image
import pypandoc
from dotenv import load_dotenv

# Try importing quill, fallback to normal text area if it fails
try:
    from streamlit_quill import st_quill
    HAS_QUILL = True
except ImportError:
    HAS_QUILL = False

# Setup Page
st.set_page_config(page_title="المترجم الذكي للصور والملفات", layout="wide", page_icon="🌐")

# Check Pandoc
try:
    pypandoc.get_pandoc_version()
except OSError:
    pypandoc.download_pandoc()

# Load API Key
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY", "")
if not api_key:
    st.error("مفتاح GEMINI_API_KEY غير موجود في ملف .env!")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"خطأ في تهيئة نموذج Gemini: {e}")
    st.stop()

st.title("المترجم الذكي المتقدم 🚀")
st.markdown("قم برفع صور أو ملفات PDF أو لصق نصوص، وسنقوم باستخراج النص وترجمته إلى العربية مع الاحتفاظ بالمعادلات الرياضية، ثم تصديره كملف Word.")

if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""
if "html_text" not in st.session_state:
    st.session_state.html_text = ""

tab_image, tab_text, tab_pdf = st.tabs(["📸 رفع صور متعددة", "📝 لصق نص من الذكاء الاصطناعي", "📄 رفع ملف PDF"])

import markdown
import markdownify

def convert_md_to_html(markdown_text):
    # Convert AI Markdown to HTML via python-markdown so equations are left as raw text
    # This prevents Quill from mangling Math equations.
    try:
        return markdown.markdown(markdown_text)
    except Exception as e:
        print(f"Error parsing markdown to html: {e}")
        return markdown_text

def generate_word_doc(text, is_html=False):
    fd, temp_path = tempfile.mkstemp(suffix='.docx')
    os.close(fd)
    
    # We use Pandoc's metadata argument (-M) to globally force Right-To-Left (RTL) in the Word document
    extra_args = ['-M', 'dir=rtl']
    
    try:
        if is_html:
            # HTML from Quill editor. We use markdownify to safely restore equations back to clean markdown.
            clean_md = markdownify.markdownify(text)
            pypandoc.convert_text(
                source=clean_md, 
                to='docx', 
                format='markdown+tex_math_dollars', 
                outputfile=temp_path,
                extra_args=extra_args
            )
        else:
            # Raw Markdown, also enabling math dollar parsing
            pypandoc.convert_text(
                source=text, 
                to='docx', 
                format='markdown+tex_math_dollars', 
                outputfile=temp_path,
                extra_args=extra_args
            )
            
        with open(temp_path, 'rb') as f:
            return f.read()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

with tab_image:
    st.subheader("رفع واستخراج النص من الصور")
    uploaded_images = st.file_uploader("اختر صورة أو أكثر", type=['png', 'jpg', 'jpeg', 'webp'], accept_multiple_files=True)
    
    if st.button("بدء المعالجة 📸", key="btn_img") and uploaded_images:
        with st.spinner("جاري استخراج النص والترجمة..."):
            prompt = (
                "Extract all the text from these images and translate it directly into Arabic. "
                "Do not include any extra conversation, explanations, or introductory text; only provide the translated Arabic text. "
                "If there are any math equations, format them properly using LaTeX dollar signs."
            )
            try:
                images = [Image.open(img) for img in uploaded_images]
                response = model.generate_content([prompt] + images)
                st.session_state.translated_text = response.text
                st.session_state.html_text = convert_md_to_html(response.text)
                st.success("تمت المعالجة بنجاح! انتقل للأسفل لتعديل وتحميل النص.")
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

with tab_text:
    st.subheader("لصق ومعالجة النص")
    pasted_text = st.text_area("قم بلصق النص الأجنبي هنا", height=200)
    
    if st.button("بدء الترجمة 📝", key="btn_text") and pasted_text:
        with st.spinner("جاري الترجمة..."):
            prompt = f"""
            Translate the following text into Arabic. 
            Do not include any extra conversation or introductory text; only provide the translated Arabic text. 
            Preserve math equations natively using LaTeX dollar signs.
            
            Text:
            {pasted_text}
            """
            try:
                response = model.generate_content(prompt)
                st.session_state.translated_text = response.text
                st.session_state.html_text = convert_md_to_html(response.text)
                st.success("تمت الترجمة بنجاح! انتقل للأسفل للتعديل.")
            except Exception as e:
                st.error(f"حدث خطأ: {e}")

with tab_pdf:
    st.subheader("رفع ومعالجة مستند PDF")
    uploaded_pdf = st.file_uploader("اختر ملف PDF", type=['pdf'])
    
    if st.button("بدء المعالجة 📄", key="btn_pdf") and uploaded_pdf:
        with st.spinner("جاري رفع واستخراج النص من الـ PDF..."):
            fd, temp_pdf_path = tempfile.mkstemp(suffix=".pdf")
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_pdf.getbuffer())
            
            try:
                gemini_file = genai.upload_file(temp_pdf_path, mime_type="application/pdf")
                prompt = (
                    "Extract all the text from this document and translate it directly into Arabic. "
                    "Do not include any extra conversation, explanations, or introductory text; only provide the translated Arabic text. "
                    "If there are any math equations, format them properly using LaTeX dollar signs."
                )
                response = model.generate_content([prompt, gemini_file])
                st.session_state.translated_text = response.text
                st.session_state.html_text = convert_md_to_html(response.text)
                genai.delete_file(gemini_file.name)
                st.success("تمت المعالجة بنجاح! انتقل للأسفل للتحميل.")
            except Exception as e:
                st.error(f"حدث خطأ: {e}")
            finally:
                os.close(fd)
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)

st.divider()

if st.session_state.translated_text:
    st.subheader("تعديل النص المترجم ✍️")
    st.info("قم بتعديل النص كما يظهر لك في المحرر.")
    
    if HAS_QUILL:
        # Give user option to use rich text (Word like) or raw Markdown
        editor_type = st.radio("اختر نوع المحرر:", ["محرر نصوص متقدم (كأنه Word)", "محرر نص خام (أفضل للمعادلات)"])
        
        if editor_type == "محرر نصوص متقدم (كأنه Word)":
            # The value fed into quill must be HTML so that bold and headings are seen properly!
            edited_text = st_quill(value=st.session_state.html_text, html=True, key="quill_editor")
            is_html = True
        else:
            edited_text = st.text_area("النص المترجم (Raw):", value=st.session_state.translated_text, height=400)
            is_html = False
    else:
        edited_text = st.text_area("النص المترجم (Raw):", value=st.session_state.translated_text, height=400)
        is_html = False

    if st.button("تحديث النص المؤقت"):
        if is_html:
            st.session_state.html_text = edited_text
        else:
            st.session_state.translated_text = edited_text
            st.session_state.html_text = convert_md_to_html(edited_text)
        st.success("تم تحديث النص.")

    if edited_text:
        try:
            docx_data = generate_word_doc(edited_text, is_html=is_html)
            st.download_button(
                label="📥 تحميل كـ Word",
                data=docx_data,
                file_name="Translated_Document.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"حدث خطأ في تجهيز ملف Word: {e}")
