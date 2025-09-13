#!/usr/bin/env python3
"""
Script to add dummy news and notices for stocks in the portfolio.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import uuid

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.database import get_db, engine
from src.models.stock import Stock
from src.models.news_notice import NewsNotice, NewsNoticeType
from sqlalchemy.orm import Session


def add_dummy_news():
    """Add dummy news and notices for existing stocks."""
    
    db = Session(engine)
    
    try:
        # Get all stocks
        stocks = db.query(Stock).all()
        
        if not stocks:
            print("❌ No stocks found. Add stocks first.")
            return
            
        print(f"✅ Found {len(stocks)} stocks. Adding news and notices...")
        
        # News data for each stock
        news_templates = {
            "AAPL": [
                {
                    "title": "Apple Reports Strong Q4 2024 Earnings",
                    "summary": "Apple Inc. reported better-than-expected quarterly results with revenue of $119.7 billion.",
                    "content": "Apple Inc. (NASDAQ: AAPL) today announced financial results for its fiscal 2024 fourth quarter ended September 28, 2024. The Company posted quarterly revenue of $119.7 billion, up 6 percent year over year, and quarterly earnings per diluted share of $1.64.",
                    "notice_type": NewsNoticeType.EARNINGS,
                    "source": "Apple Inc.",
                    "external_url": "https://investor.apple.com/news-and-events/news-releases/",
                    "document_url": "/documents/aapl-q4-2024-earnings.pdf",
                    "days_ago": 5
                },
                {
                    "title": "Apple Announces New MacBook Pro with M4 Chip",
                    "summary": "Apple unveiled the latest MacBook Pro featuring the powerful M4 chip with enhanced performance.",
                    "content": "Apple today announced the new MacBook Pro featuring the M4 family of chips, bringing even more power and capability to the world's best pro laptop.",
                    "notice_type": NewsNoticeType.PRESS_RELEASE,
                    "source": "Apple Newsroom",
                    "external_url": "https://www.apple.com/newsroom/",
                    "document_url": "/documents/aapl-macbook-pro-m4-announcement.pdf",
                    "days_ago": 12
                },
                {
                    "title": "Apple Declares Quarterly Dividend",
                    "summary": "Apple's Board of Directors declared a cash dividend of $0.25 per share.",
                    "content": "Apple's Board of Directors has declared a cash dividend of $0.25 per share of the Company's common stock. The dividend is payable on November 14, 2024 to shareholders of record as of the close of business on November 11, 2024.",
                    "notice_type": NewsNoticeType.DIVIDEND,
                    "source": "Apple Inc.",
                    "external_url": "https://investor.apple.com/",
                    "document_url": "/documents/aapl-dividend-declaration-q4-2024.pdf",
                    "days_ago": 8
                }
            ],
            "GOOGL": [
                {
                    "title": "Alphabet Reports Third Quarter 2024 Results",
                    "summary": "Alphabet Inc. reported total revenues of $88.3 billion for Q3 2024.",
                    "content": "Alphabet Inc. (NASDAQ: GOOGL) today announced financial results for the quarter ended September 30, 2024. Total revenues were $88.3 billion, an increase of 15% year over year.",
                    "notice_type": NewsNoticeType.EARNINGS,
                    "source": "Alphabet Inc.",
                    "external_url": "https://abc.xyz/investor/",
                    "document_url": "/documents/googl-q3-2024-earnings.pdf",
                    "days_ago": 3
                },
                {
                    "title": "Google Cloud Announces New AI Capabilities",
                    "summary": "Google Cloud unveiled new generative AI features for enterprise customers.",
                    "content": "Google Cloud today announced new AI-powered capabilities designed to help enterprises accelerate their digital transformation with generative AI.",
                    "notice_type": NewsNoticeType.PRESS_RELEASE,
                    "source": "Google Cloud",
                    "external_url": "https://cloud.google.com/blog/",
                    "document_url": "/documents/googl-cloud-ai-announcement.pdf",
                    "days_ago": 15
                }
            ],
            "MSFT": [
                {
                    "title": "Microsoft Reports Record Q1 FY25 Results",
                    "summary": "Microsoft delivered strong financial results with revenue of $65.6 billion.",
                    "content": "Microsoft Corp. today announced the following results for the quarter ended September 30, 2024. Revenue was $65.6 billion and increased 16% (up 15% in constant currency).",
                    "notice_type": NewsNoticeType.EARNINGS,
                    "source": "Microsoft Corp.",
                    "external_url": "https://www.microsoft.com/en-us/Investor/",
                    "document_url": "/documents/msft-q1-fy25-earnings.pdf",
                    "days_ago": 7
                },
                {
                    "title": "Microsoft Copilot Integration Expands",
                    "summary": "Microsoft announced broader integration of Copilot across Office 365 suite.",
                    "content": "Microsoft today announced the expansion of Microsoft Copilot integration across the entire Office 365 suite, bringing AI-powered productivity to millions of users.",
                    "notice_type": NewsNoticeType.PRESS_RELEASE,
                    "source": "Microsoft News",
                    "external_url": "https://news.microsoft.com/",
                    "document_url": "/documents/msft-copilot-expansion.pdf",
                    "days_ago": 18
                }
            ],
            "TSLA": [
                {
                    "title": "Tesla Delivers Record Q3 2024 Vehicle Deliveries",
                    "summary": "Tesla delivered 462,890 vehicles in Q3 2024, exceeding expectations.",
                    "content": "Tesla delivered 462,890 vehicles in Q3 2024, a new quarterly record that exceeded Wall Street expectations.",
                    "notice_type": NewsNoticeType.PRESS_RELEASE,
                    "source": "Tesla, Inc.",
                    "external_url": "https://ir.tesla.com/",
                    "document_url": "/documents/tsla-q3-2024-deliveries.pdf",
                    "days_ago": 10
                },
                {
                    "title": "Tesla Cybertruck Production Update",
                    "summary": "Tesla provides update on Cybertruck manufacturing and delivery timeline.",
                    "content": "Tesla announced significant progress in Cybertruck production, with manufacturing now reaching target capacity at the Texas Gigafactory.",
                    "notice_type": NewsNoticeType.PRESS_RELEASE,
                    "source": "Tesla, Inc.",
                    "external_url": "https://www.tesla.com/",
                    "document_url": "/documents/tsla-cybertruck-production-update.pdf",
                    "days_ago": 22
                },
                {
                    "title": "Tesla Stock Split Proposal",
                    "summary": "Tesla Board proposes 3-for-1 stock split subject to shareholder approval.",
                    "content": "Tesla's Board of Directors has approved a proposal for a 3-for-1 stock split, subject to shareholder approval at the upcoming annual meeting.",
                    "notice_type": NewsNoticeType.CORPORATE_ACTION,
                    "source": "Tesla, Inc.",
                    "external_url": "https://ir.tesla.com/",
                    "document_url": "/documents/tsla-stock-split-proposal.pdf",
                    "days_ago": 4
                }
            ],
            "AMZN": [
                {
                    "title": "Amazon Reports Strong Q3 2024 Results",
                    "summary": "Amazon.com Inc. reported net sales of $158.9 billion for Q3 2024.",
                    "content": "Amazon.com, Inc. today announced financial results for its third quarter ended September 30, 2024. Net sales increased 11% to $158.9 billion in the third quarter.",
                    "notice_type": NewsNoticeType.EARNINGS,
                    "source": "Amazon.com, Inc.",
                    "external_url": "https://ir.aboutamazon.com/",
                    "document_url": "/documents/amzn-q3-2024-earnings.pdf",
                    "days_ago": 6
                },
                {
                    "title": "Amazon Web Services Launches New AI Services",
                    "summary": "AWS introduced new machine learning and AI services for enterprise customers.",
                    "content": "Amazon Web Services announced the launch of several new artificial intelligence and machine learning services designed to help enterprises build and deploy AI applications at scale.",
                    "notice_type": NewsNoticeType.PRESS_RELEASE,
                    "source": "Amazon Web Services",
                    "external_url": "https://aws.amazon.com/blogs/",
                    "document_url": "/documents/amzn-aws-ai-services.pdf",
                    "days_ago": 14
                }
            ]
        }
        
        news_count = 0
        base_date = datetime.now()
        
        for stock in stocks:
            if stock.symbol in news_templates:
                news_items = news_templates[stock.symbol]
                
                for news_item in news_items:
                    # Check if news already exists
                    existing_news = db.query(NewsNotice).filter(
                        NewsNotice.stock_id == stock.id,
                        NewsNotice.title == news_item["title"]
                    ).first()
                    
                    if existing_news:
                        print(f"📰 News '{news_item['title']}' already exists for {stock.symbol}")
                        continue
                    
                    news_notice = NewsNotice(
                        id=uuid.uuid4(),
                        stock_id=stock.id,
                        title=news_item["title"],
                        summary=news_item["summary"],
                        content=news_item["content"],
                        notice_type=news_item["notice_type"],
                        published_date=base_date - timedelta(days=news_item["days_ago"]),
                        source=news_item["source"],
                        external_url=news_item["external_url"],
                        document_url=news_item["document_url"]
                    )
                    
                    db.add(news_notice)
                    news_count += 1
                    print(f"📰 Created news: {news_item['title']} for {stock.symbol}")
        
        db.commit()
        
        print(f"\n✅ Successfully added {news_count} news/notices items!")
        print(f"You can now view individual holding pages to see the timeline!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error adding dummy news data: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    print("🗞️  Adding dummy news and notices for stocks...")
    add_dummy_news()
    print("✅ Done!")