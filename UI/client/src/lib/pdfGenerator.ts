import { jsPDF } from 'jspdf';
import { marked } from 'marked';

interface PDFOptions {
  title?: string;
  fontSize?: number;
  lineHeight?: number;
  margin?: number;
}

export async function generatePDFFromMarkdown(
  markdown: string,
  options: PDFOptions = {}
): Promise<void> {
  const {
    title = 'Incident Analysis Report',
    fontSize = 11,
    lineHeight = 1.5,
    margin = 20
  } = options;

  const pdf = new jsPDF({
    orientation: 'portrait',
    unit: 'mm',
    format: 'a4'
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const maxWidth = pageWidth - (margin * 2);
  let yPosition = margin;
  const lineHeightMM = fontSize * lineHeight * 0.352778;

  pdf.setFontSize(16);
  pdf.setFont('helvetica', 'bold');
  pdf.text(title, margin, yPosition);
  yPosition += lineHeightMM * 2;

  pdf.setDrawColor(100, 100, 100);
  pdf.line(margin, yPosition, pageWidth - margin, yPosition);
  yPosition += lineHeightMM * 1.5;

  const html = await marked.parse(markdown);
  const parser = new DOMParser();
  const doc = parser.parseFromString(html as string, 'text/html');
  const body = doc.body;

  const processNode = (node: Node, depth: number = 0): void => {
    if (yPosition > pageHeight - margin - 20) {
      pdf.addPage();
      yPosition = margin;
    }

    if (node.nodeType === Node.TEXT_NODE) {
      const text = node.textContent?.trim() || '';
      if (text) {
        const lines = pdf.splitTextToSize(text, maxWidth);
        for (const line of lines) {
          if (yPosition > pageHeight - margin - 20) {
            pdf.addPage();
            yPosition = margin;
          }
          pdf.setFontSize(fontSize);
          pdf.setFont('helvetica', 'normal');
          pdf.text(line, margin, yPosition);
          yPosition += lineHeightMM;
        }
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      const element = node as HTMLElement;
      const tagName = element.tagName.toLowerCase();

      switch (tagName) {
        case 'h1':
          if (yPosition > pageHeight - margin - 30) {
            pdf.addPage();
            yPosition = margin;
          }
          pdf.setFontSize(fontSize + 6);
          pdf.setFont('helvetica', 'bold');
          yPosition += lineHeightMM * 0.5;
          const h1Text = element.textContent?.trim() || '';
          if (h1Text) {
            pdf.text(h1Text, margin, yPosition);
            yPosition += lineHeightMM * 1.5;
          }
          break;

        case 'h2':
          if (yPosition > pageHeight - margin - 25) {
            pdf.addPage();
            yPosition = margin;
          }
          pdf.setFontSize(fontSize + 4);
          pdf.setFont('helvetica', 'bold');
          yPosition += lineHeightMM * 0.5;
          const h2Text = element.textContent?.trim() || '';
          if (h2Text) {
            pdf.text(h2Text, margin, yPosition);
            yPosition += lineHeightMM * 1.2;
          }
          break;

        case 'h3':
          if (yPosition > pageHeight - margin - 20) {
            pdf.addPage();
            yPosition = margin;
          }
          pdf.setFontSize(fontSize + 2);
          pdf.setFont('helvetica', 'bold');
          yPosition += lineHeightMM * 0.3;
          const h3Text = element.textContent?.trim() || '';
          if (h3Text) {
            pdf.text(h3Text, margin, yPosition);
            yPosition += lineHeightMM;
          }
          break;

        case 'p':
          yPosition += lineHeightMM * 0.3;
          for (const child of Array.from(element.childNodes)) {
            processNode(child, depth);
          }
          yPosition += lineHeightMM * 0.5;
          break;

        case 'ul':
        case 'ol':
          yPosition += lineHeightMM * 0.3;
          const listItems = element.querySelectorAll('li');
          listItems.forEach((li, index) => {
            if (yPosition > pageHeight - margin - 20) {
              pdf.addPage();
              yPosition = margin;
            }
            const prefix = tagName === 'ol' ? `${index + 1}. ` : '• ';
            const text = li.textContent?.trim() || '';
            if (text) {
              pdf.setFontSize(fontSize);
              pdf.setFont('helvetica', 'normal');
              const lines = pdf.splitTextToSize(prefix + text, maxWidth - 5);
              for (let i = 0; i < lines.length; i++) {
                if (i === 0) {
                  pdf.text(lines[i], margin + 5, yPosition);
                } else {
                  pdf.text(lines[i], margin + 10, yPosition);
                }
                yPosition += lineHeightMM;
              }
            }
          });
          yPosition += lineHeightMM * 0.3;
          break;

        case 'code':
          pdf.setFont('courier', 'normal');
          pdf.setFontSize(fontSize - 1);
          const codeText = element.textContent?.trim() || '';
          if (codeText) {
            const lines = pdf.splitTextToSize(codeText, maxWidth - 10);
            for (const line of lines) {
              if (yPosition > pageHeight - margin - 20) {
                pdf.addPage();
                yPosition = margin;
              }
              pdf.text(line, margin + 5, yPosition);
              yPosition += lineHeightMM;
            }
          }
          pdf.setFont('helvetica', 'normal');
          break;

        case 'pre':
          yPosition += lineHeightMM * 0.5;
          pdf.setFont('courier', 'normal');
          pdf.setFontSize(fontSize - 1);
          const preText = element.textContent?.trim() || '';
          if (preText) {
            const lines = pdf.splitTextToSize(preText, maxWidth - 10);
            for (const line of lines) {
              if (yPosition > pageHeight - margin - 20) {
                pdf.addPage();
                yPosition = margin;
              }
              pdf.text(line, margin + 5, yPosition);
              yPosition += lineHeightMM;
            }
          }
          pdf.setFont('helvetica', 'normal');
          yPosition += lineHeightMM * 0.5;
          break;

        case 'strong':
        case 'b':
          pdf.setFont('helvetica', 'bold');
          for (const child of Array.from(element.childNodes)) {
            processNode(child, depth);
          }
          pdf.setFont('helvetica', 'normal');
          break;

        case 'em':
        case 'i':
          pdf.setFont('helvetica', 'italic');
          for (const child of Array.from(element.childNodes)) {
            processNode(child, depth);
          }
          pdf.setFont('helvetica', 'normal');
          break;

        case 'blockquote':
          yPosition += lineHeightMM * 0.5;
          pdf.setDrawColor(150, 150, 150);
          pdf.line(margin + 3, yPosition - lineHeightMM, margin + 3, yPosition + lineHeightMM * 2);
          for (const child of Array.from(element.childNodes)) {
            processNode(child, depth);
          }
          yPosition += lineHeightMM * 0.5;
          break;

        case 'hr':
          yPosition += lineHeightMM;
          pdf.setDrawColor(150, 150, 150);
          pdf.line(margin, yPosition, pageWidth - margin, yPosition);
          yPosition += lineHeightMM;
          break;

        default:
          for (const child of Array.from(element.childNodes)) {
            processNode(child, depth);
          }
          break;
      }
    } else {
      for (const child of Array.from(node.childNodes)) {
        processNode(child, depth);
      }
    }
  };

  for (const child of Array.from(body.childNodes)) {
    processNode(child);
  }

  const timestamp = new Date().toISOString().split('T')[0];
  const filename = `REPORT_GEN_V2_${timestamp}.pdf`;
  pdf.save(filename);
}

