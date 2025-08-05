import os
from dotenv import load_dotenv
from gpt_researcher.scraper.firecrawl.firecrawl import FireCrawl
import requests
import json
from datetime import datetime

load_dotenv()

def test_firecrawl_scraping():
    """Test FireCrawl scraping with detailed debugging and save results to markdown file"""
    
    # Define output folder and create if it doesn't exist
    output_folder = "1A_Firecrawl_scraped_content_results"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Create timestamp for unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_folder, f"firecrawl_scraping_results_{timestamp}.md")
    
    # Test URLs from your prompt
    test_urls = [
        "https://liveaboardindonesia.com"
        # "https://www.liveaboard.com/",
        # "https://premierliveaboarddiving.com/destination/komodo",
        # "https://www.divingsquad.com/scuba-diving-komodo/",
        # "https://www.rainforestcruises.com"
    ]
    
    # Create a session for the scraper
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    # Initialize markdown content
    markdown_content = []
    markdown_content.append(f"# FireCrawl Scraping Results")
    markdown_content.append(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    markdown_content.append(f"**Total URLs tested:** {len(test_urls)}")
    markdown_content.append("")
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n{'='*80}")
        print(f"Testing URL {i}/{len(test_urls)}: {url}")
        print('='*80)
        
        # Add URL section to markdown
        markdown_content.append(f"## URL {i}: {url}")
        markdown_content.append("")
        
        try:
            # Test direct FireCrawl
            scraper = FireCrawl(url, session=session)
            
            # Get the raw response first
            print("Getting raw FireCrawl response...")
            response = scraper.firecrawl.scrape_url(url=url, formats=["markdown"])
            
            # Debug info for console
            print(f"Response type: {type(response)}")
            print(f"Response attributes: {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            # Add technical details to markdown
            markdown_content.append("### Technical Details")
            markdown_content.append(f"- **Response Type:** `{type(response)}`")
            markdown_content.append(f"- **Response Attributes:** {[attr for attr in dir(response) if not attr.startswith('_')]}")
            
            if hasattr(response, 'success'):
                print(f"Success: {response.success}")
                markdown_content.append(f"- **Success:** {response.success}")
            
            if hasattr(response, 'error'):
                print(f"Error: {response.error}")
                markdown_content.append(f"- **Error:** {response.error}")
            
            markdown_content.append("")
            
            # Process metadata
            metadata_info = {}
            if hasattr(response, 'metadata'):
                print(f"\nMETADATA:")
                print(f"Metadata type: {type(response.metadata)}")
                
                markdown_content.append("### Metadata")
                markdown_content.append(f"**Type:** `{type(response.metadata)}`")
                markdown_content.append("")
                
                if hasattr(response.metadata, 'statusCode'):
                    print(f"Status Code: {response.metadata.statusCode}")
                    metadata_info['statusCode'] = response.metadata.statusCode
                if hasattr(response.metadata, 'title'):
                    print(f"Title: {response.metadata.title}")
                    metadata_info['title'] = response.metadata.title
                if hasattr(response.metadata, 'description'):
                    print(f"Description: {response.metadata.description}")
                    metadata_info['description'] = response.metadata.description
                if hasattr(response.metadata, 'language'):
                    print(f"Language: {response.metadata.language}")
                    metadata_info['language'] = response.metadata.language
                if hasattr(response.metadata, 'sourceURL'):
                    print(f"Source URL: {response.metadata.sourceURL}")
                    metadata_info['sourceURL'] = response.metadata.sourceURL
                elif isinstance(response.metadata, dict):
                    print(f"Metadata dict: {json.dumps(response.metadata, indent=2, default=str)}")
                    metadata_info = response.metadata
                
                # Add metadata to markdown
                for key, value in metadata_info.items():
                    markdown_content.append(f"- **{key}:** {value}")
                markdown_content.append("")
            
            # Process content
            content_from_raw = None
            if hasattr(response, 'data'):
                print(f"\nRAW DATA:")
                print(f"Data type: {type(response.data)}")
                if response.data:
                    print(f"Data attributes: {[attr for attr in dir(response.data) if not attr.startswith('_')]}")
                    if hasattr(response.data, 'markdown'):
                        content_from_raw = response.data.markdown
                        print(f"Markdown content length: {len(content_from_raw) if content_from_raw else 0}")
                    elif isinstance(response.data, dict) and 'markdown' in response.data:
                        content_from_raw = response.data['markdown']
                        print(f"Markdown content length: {len(content_from_raw) if content_from_raw else 0}")
                else:
                    print("Data is None or empty")
            elif hasattr(response, 'markdown'):
                content_from_raw = response.markdown
                print(f"\nDIRECT MARKDOWN:")
                print(f"Markdown content length: {len(content_from_raw) if content_from_raw else 0}")
            
            # Test the scraper method
            print(f"\n{'='*50} SCRAPER METHOD RESULTS {'='*50}")
            content, images, title = scraper.scrape()
            print(f"Scrape result - Content length: {len(content)}, Images: {len(images)}, Title: '{title}'")
            
            # Add scraper results to markdown
            markdown_content.append("### Scraper Method Results")
            markdown_content.append(f"- **Content Length:** {len(content)}")
            markdown_content.append(f"- **Images Found:** {len(images)}")
            markdown_content.append(f"- **Title:** {title}")
            markdown_content.append("")
            
            # Add raw content to markdown
            if content_from_raw:
                markdown_content.append("### Raw Content from FireCrawl")
                markdown_content.append(f"**Length:** {len(content_from_raw)} characters")
                markdown_content.append("")
                markdown_content.append("```markdown")
                markdown_content.append(content_from_raw)
                markdown_content.append("```")
                markdown_content.append("")
            
            # Add processed content to markdown
            if content:
                markdown_content.append("### Processed Content from Scraper")
                markdown_content.append(f"**Length:** {len(content)} characters")
                markdown_content.append("")
                markdown_content.append("```markdown")
                markdown_content.append(content)
                markdown_content.append("```")
                markdown_content.append("")
            
            # Add images to markdown
            if images:
                markdown_content.append("### Images Found")
                for j, img in enumerate(images, 1):
                    markdown_content.append(f"{j}. {img}")
                markdown_content.append("")
            
            # Add comparison
            if content_from_raw and content:
                markdown_content.append("### Content Comparison")
                markdown_content.append(f"- **Raw content length:** {len(content_from_raw)}")
                markdown_content.append(f"- **Processed content length:** {len(content)}")
                markdown_content.append(f"- **Content identical:** {content_from_raw == content}")
                
                if content_from_raw != content:
                    markdown_content.append("- **Note:** Contents differ")
                    markdown_content.append("")
                    markdown_content.append("#### First 500 characters comparison:")
                    markdown_content.append("**Raw:**")
                    markdown_content.append("```")
                    markdown_content.append(content_from_raw[:500] + "...")
                    markdown_content.append("```")
                    markdown_content.append("**Processed:**")
                    markdown_content.append("```")
                    markdown_content.append(content[:500] + "...")
                    markdown_content.append("```")
                markdown_content.append("")
                
        except Exception as e:
            error_msg = f"Error testing {url}: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # Add error to markdown
            markdown_content.append("### Error")
            markdown_content.append(f"```")
            markdown_content.append(error_msg)
            markdown_content.append("```")
            markdown_content.append("")
        
        markdown_content.append("---")
        markdown_content.append("")
        print("-" * 80)
    
    # Write markdown content to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(markdown_content))
        
        print(f"\n{'='*80}")
        print(f"✅ Results saved to: {output_file}")
        print(f"📁 Full path: {os.path.abspath(output_file)}")
        print(f"📊 Total lines written: {len(markdown_content)}")
        print('='*80)
        
    except Exception as e:
        print(f"❌ Error saving to file: {str(e)}")

if __name__ == "__main__":
    # Check if FireCrawl API key is set
    if not os.environ.get('FIRECRAWL_API_KEY'):
        print("ERROR: FIRECRAWL_API_KEY environment variable not set!")
        exit(1)
    
    test_firecrawl_scraping()