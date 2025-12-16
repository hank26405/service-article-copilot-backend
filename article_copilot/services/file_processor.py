import io
from typing import Tuple, Any, List
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
# 第三方庫 (需確保 requirements.txt 有安裝)
# pypdf, python-docx, python-pptx, pandas, openpyxl, pillow
import pandas as pd
import pypdf
from docx import Document as DocxDocument
from pptx import Presentation as PptxPresentation
from PIL import Image
import json

# 模擬 LangChain 呼叫 (實際專案需 import 真實的 ChatOpenAI)
# from langchain_openai import ChatOpenAI
# from langchain_core.messages import HumanMessage, SystemMessage

class BaseFileProcessor(ABC):
    @abstractmethod
    def process(self, content: bytes, filename: str) -> Tuple[Any, str, int]:
        """
        處理檔案並回傳:
        1. display_data (HTML/URL/List)
        2. llm_context (Markdown)
        3. page_count
        """
        pass

class ExcelProcessor(BaseFileProcessor):
    def process(self, content: bytes, filename: str) -> Tuple[str, str, int]:
        """處理 Excel: Display=HTML, LLM=Markdown"""
        try:
            # 讀取 Excel
            df = pd.read_excel(io.BytesIO(content))
            
            # 1. Display: 保留基本樣式的 HTML (這裡簡化處理，實際可用 style)
            # 使用 table class 讓前端可以用 Tailwind 美化
            display_html = df.to_html(index=False, classes="min-w-full border-collapse border border-gray-300")
            
            # 2. LLM: Markdown
            llm_md = f"### Data from {filename}\n\n" + df.to_markdown(index=False)
            
            return display_html, llm_md, 1
        except Exception as e:
            return f"<div>Error parsing Excel: {e}</div>", f"Error parsing file: {e}", 0

class PDFProcessor(BaseFileProcessor):
    def process(self, content: bytes, filename: str) -> Tuple[str, str, int]:
        """處理 PDF: Display=API_URL(外部設定), LLM=Text with Page Numbers"""
        try:
            llm_text = ""
            page_count = 0
            
            with io.BytesIO(content) as f:
                reader = pypdf.PdfReader(f)
                page_count = len(reader.pages)
                
                for i, page in enumerate(reader.pages):
                    text = page.extract_text()
                    llm_text += f"\n\n## --- Page {i+1} ---\n{text}"
            
            # Display Data 由 Service 層設為 "/api/materials/{id}/raw"
            # 這裡回傳 placeholder，Service 會覆蓋它
            return "__API_URL_PLACEHOLDER__", llm_text, page_count
        except Exception as e:
            return "", f"Error parsing PDF: {e}", 0

class DocxProcessor(BaseFileProcessor):
    def process(self, content: bytes, filename: str) -> Tuple[str, str, int]:
        """處理 Word: Display=HTML(Conversion), LLM=Markdown"""
        try:
            doc = DocxDocument(io.BytesIO(content))
            
            full_text = []
            html_parts = []
            
            # 簡單轉換邏輯
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    full_text.append(text)
                    html_parts.append(f"<p class='mb-2'>{text}</p>")
            
            # 表格處理 (簡易版)
            for table in doc.tables:
                rows_data = []
                for row in table.rows:
                    rows_data.append([cell.text for cell in row.cells])
                
                # 轉 Markdown
                df = pd.DataFrame(rows_data)
                if not df.empty:
                    md_table = df.to_markdown(index=False, header=False)
                    full_text.append(f"\n{md_table}\n")
                    
                    # 轉 HTML
                    html_table = df.to_html(index=False, header=False, classes="border")
                    html_parts.append(html_table)
            
            display_html = "".join(html_parts)
            llm_md = "\n".join(full_text)
            
            return display_html, llm_md, 1 # Word 頁數難估算，暫定 1
        except Exception as e:
            return "", f"Error parsing Docx: {e}", 0

class PptxProcessor(BaseFileProcessor):
    def process(self, content: bytes, filename: str) -> Tuple[List[str], str, int]:
        """處理 PPT: Display=Image URLs(Placeholder), LLM=Text+Notes+Vision"""
        try:
            prs = PptxPresentation(io.BytesIO(content))
            llm_context = ""
            page_count = 0
            
            for i, slide in enumerate(prs.slides):
                page_count += 1
                llm_context += f"\n\n## --- Slide {i+1} ---\n"
                
                # 1. 標題
                if slide.shapes.title:
                    llm_context += f"### Title: {slide.shapes.title.text}\n"
                
                # 2. 內文
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape != slide.shapes.title:
                        text = shape.text.strip()
                        if text:
                            llm_context += f"- {text}\n"
                
                # 3. 備忘稿 (Speaker Notes)
                if slide.has_notes_slide:
                    notes = slide.notes_slide.notes_text_frame.text
                    if notes:
                        llm_context += f"> **Speaker Notes**: {notes}\n"
                
                # 4. Vision Analysis (Mock)
                # 實際專案需: slide截圖 -> base64 -> Vision Model -> Description
                # 這裡暫時放入一個 placeholder 說明
                llm_context += "\n[Visual Analysis]: (Requires integration with Vision Model to extract chart data from slide screenshot)\n"

            # Display Data 由 Service 層處理 (需轉檔為圖片)
            # 這裡回傳 placeholder list
            return ["__SLIDE_IMAGES_PLACEHOLDER__"], llm_context, page_count
        except Exception as e:
            return [], f"Error parsing PPT: {e}", 0

class ImageProcessor(BaseFileProcessor):
    def process(self, content: bytes, filename: str) -> Tuple[str, str, int]:
        """處理 Image: Display=API_URL, LLM=Vision Analysis"""
        
        # 1. Vision Model Analysis (Unified Pipeline)
        # 呼叫 LLM 進行單次分析 (Document/Chart/Photo)
        
        # --- Mock Logic Start (模擬 LLM 回應) ---
        # 實際應呼叫 ChatOpenAI(model="gpt-4o-mini")...
        mock_analysis = f"[Vision Analysis for {filename}]\n"
        mock_analysis += "- Type: Detected as a Data Chart\n"
        mock_analysis += "- Content: Shows a 20% increase in revenue for Q3.\n"
        mock_analysis += "| Quarter | Revenue |\n|---|---|\n| Q2 | 100M |\n| Q3 | 120M |"
        # --- Mock Logic End ---
        
        llm_context = mock_analysis
        
        # Display Data 由 Service 層設為 API URL
        return "__API_URL_PLACEHOLDER__", llm_context, 1

class HtmlTableProcessor(BaseFileProcessor):
    """
    專門處理從 Excel/網頁貼上的 HTML 表格、JSON 或純文字。
    
    支援:
    1. HTML Table (包括 Excel/Word 複雜貼上帶來的 Multi-level Headers)
    2. 純 JSON 字串
    3. 純文字 (Plain Text)
    """

    def _flatten_multi_index(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        輔助方法：將 DataFrame 的 MultiIndex Column 扁平化為單行字串。
        例如: 將 ('復健', '基本數據', '身高') 轉換為 '復健 - 基本數據 - 身高'，並清理空值。
        """
        if isinstance(df.columns, pd.MultiIndex):
            df_copy = df.copy()
            new_cols = []
            # 迭代 MultiIndex 的每一組標頭
            for col_tuple in df_copy.columns:
                # 過濾掉 None, NaN, 或空字串
                clean_parts = [
                    str(part).strip() for part in col_tuple 
                    if pd.notna(part) and str(part).strip()
                ]
                # 用 ' - ' 連接，這是 LLM 易於理解的上下文格式
                new_cols.append(" - ".join(clean_parts) if clean_parts else "Unnamed Column")
            
            df_copy.columns = new_cols
            # 清理全空行和全空列
            return df_copy.dropna(how='all', axis=1).dropna(how='all', axis=0).reset_index(drop=True)
        
        # 如果不是 MultiIndex，只清理空行/空列
        return df.dropna(how='all', axis=1).dropna(how='all', axis=0).reset_index(drop=True)

    def process(self, content: bytes, filename: str) -> Tuple[str, str, int]:
        try:
            html_str = content.decode('utf-8').strip()
            
            # --- Case 1: Plain Text or JSON (非 Table 內容偵測) ---
            # 判斷是否為明顯的非表格內容 (例如，不包含 <table 標籤)
            if not '<table' in html_str.lower():
                
                # 嘗試解析為 JSON
                try:
                    data = json.loads(html_str)
                    # 格式化為 LLM 友善的 JSON code block
                    llm_context = json.dumps(data, indent=2, ensure_ascii=False)
                    # Display: 用 <pre> 標籤保留格式
                    display_html = f"<pre class='bg-gray-100 p-4 rounded text-sm whitespace-pre-wrap'>{json.dumps(data, indent=2, ensure_ascii=False)}</pre>"
                    return display_html, llm_context, 1
                except json.JSONDecodeError:
                    # 如果不是 JSON，則視為純文字
                    llm_context = html_str
                    # Display: 用 <div class='whitespace-pre-wrap'> 保留換行
                    display_html = f"<div class='whitespace-pre-wrap p-2'>{html_str}</div>"
                    return display_html, llm_context, 1
            
            # --- Case 2: HTML Table Content (包括複雜表頭) ---
            
            # 1. LLM View: 轉 Markdown
            # pandas.read_html 會自動處理 HTML 中的 rowspan/colspan 並嘗試建立 MultiIndex
            dfs = pd.read_html(io.BytesIO(content), header=None, flavor='bs4') 
            # 使用 header=None 強制讀取所有內容，再交給 _flatten_multi_index 處理表頭
            
            if not dfs:
                 # 如果 read_html 找不到 table，但前面有 <table 標記，則回傳原始 HTML
                return html_str, html_str, 1
                
            df = dfs[0] # 取第一個表格
            
            # 處理多表頭 (MultiIndex) 並清理空行/空列
            df_cleaned = self._flatten_multi_index(df)

            # 轉 Markdown，標頭已扁平化，LLM 可直接分析
            llm_md = df_cleaned.to_markdown(index=False)
            
            # 2. Display View: 清洗 HTML
            soup = BeautifulSoup(html_str, 'html.parser')
            table = soup.find('table')
            
            if table:
                # 保留原始的 HTML 表格結構（包含 rowspan/colspan）供前端視覺化呈現
                table['class'] = 'min-w-full border-collapse border border-gray-300 text-sm'
                display_html = str(table)
            else:
                display_html = html_str
            
            return display_html, llm_md, 1
            
        except Exception as e:
            return f"<div>Processing failed: {type(e).__name__}: {str(e)}</div>", f"Error during processing: {type(e).__name__}: {str(e)}", 0

# ------------------- FileProcessorFactory -------------------
class FileProcessorFactory:
    @staticmethod
    def get_processor(mime_type: str) -> BaseFileProcessor:
        if "spreadsheet" in mime_type or "excel" in mime_type:
            return ExcelProcessor()
        elif "pdf" in mime_type:
            return PDFProcessor()
        elif "word" in mime_type or "document" in mime_type:
            return DocxProcessor()
        elif "presentation" in mime_type or "powerpoint" in mime_type:
            return PptxProcessor()
        elif "image" in mime_type:
            return ImageProcessor()
        elif "html" in mime_type:
            # 處理所有貼上內容 (Text, JSON, Table)
            return HtmlTableProcessor()
        else:
            raise ValueError(f"Unsupported MIME type: {mime_type}")