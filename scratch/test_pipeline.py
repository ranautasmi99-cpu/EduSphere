import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

def create_sample_pdf(filepath="scratch/sample_lecture.pdf"):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Lecture 1: Introduction to Machine Learning", styles['Title']),
        Spacer(1, 12),
        Paragraph("Machine learning is a subset of artificial intelligence focused on building systems that learn from data. Supervised learning algorithms learn from labeled dataset inputs to predict outputs.", styles['Normal']),
        Spacer(1, 8),
        Paragraph("Key paradigms include Supervised Learning (e.g. Linear Regression, Classification), Unsupervised Learning (e.g. K-Means Clustering), and Reinforcement Learning.", styles['Normal']),
        Spacer(1, 8),
        Paragraph("Overfitting occurs when a statistical model fits exactly against its training data, capturing noise instead of underlying distribution.", styles['Normal'])
    ]
    doc.build(story)
    print(f"Sample PDF created at {filepath}")
    return filepath

if __name__ == "__main__":
    create_sample_pdf()
