import markdown
import markdownify
import pypandoc

# 1. AI outputs markdown with math
ai_output = "Here is some **bold** text and math $E=mc^2$."

# 2. We convert it to HTML using pure python markdown, which ignores $ equations
html_for_quill = markdown.markdown(ai_output)
print("HTML for Quill Editor:", repr(html_for_quill))

# 3. User edits HTML in Quill, we get it back, send it to Markdownify
md_from_quill = markdownify.markdownify(html_for_quill)
print("Markdown from Quill:", repr(md_from_quill))

# 4. We send this clean markdown to Pandoc to produce Docx!
pypandoc.convert_text(md_from_quill, to='docx', format='markdown+tex_math_dollars', outputfile='final.docx')
print("Successfully generated Word Doc with Math!")
