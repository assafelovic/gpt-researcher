from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType
from gpt_researcher.config import Config
from gpt_researcher.skills.deep_research import ResearchProgress
from gpt_researcher.utils.enum import Tone
import asyncio
import time
import os
import psutil
import threading
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

os.environ['SCRAPER'] = 'firecrawl'

# web_scraper_executor_wrapper -> other option for scrapper

class ResourceMonitor:
    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.stats = {
            'memory_mb': [],
            'cpu_percent': [],
            'system_memory_percent': [],
            'timestamps': []
        }
        self.start_time = None
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring system resources"""
        self.monitoring = True
        self.start_time = time.time()
        self.stats = {
            'memory_mb': [],
            'cpu_percent': [],
            'system_memory_percent': [],
            'timestamps': []
        }
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                current_time = time.time()
                
                # Memory usage in MB
                memory_mb = self.process.memory_info().rss / 1024 / 1024
                self.stats['memory_mb'].append(memory_mb)
                
                # CPU usage percentage
                cpu_percent = self.process.cpu_percent()
                self.stats['cpu_percent'].append(cpu_percent)
                
                # System-wide memory
                system_memory = psutil.virtual_memory()
                self.stats['system_memory_percent'].append(system_memory.percent)
                
                # Timestamp
                self.stats['timestamps'].append(current_time - self.start_time)
                
                time.sleep(1)  # Monitor every second
            except:
                break
                
    def stop_monitoring(self):
        """Stop monitoring and return stats"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        
        # Calculate final stats
        duration = time.time() - self.start_time if self.start_time else 0
        
        final_stats = {
            'duration': duration,
            'peak_memory_mb': max(self.stats['memory_mb']) if self.stats['memory_mb'] else 0,
            'avg_memory_mb': sum(self.stats['memory_mb']) / len(self.stats['memory_mb']) if self.stats['memory_mb'] else 0,
            'min_memory_mb': min(self.stats['memory_mb']) if self.stats['memory_mb'] else 0,
            'peak_cpu_percent': max(self.stats['cpu_percent']) if self.stats['cpu_percent'] else 0,
            'avg_cpu_percent': sum(self.stats['cpu_percent']) / len(self.stats['cpu_percent']) if self.stats['cpu_percent'] else 0,
            'peak_system_memory_percent': max(self.stats['system_memory_percent']) if self.stats['system_memory_percent'] else 0,
            'samples_count': len(self.stats['memory_mb']),
            'raw_stats': self.stats
        }
        
        return final_stats

def save_report_to_markdown(report: str, query: str, research_time: float, report_time: float, sources: list, prompt_index: int, depth: int, breadth: int, cost: float, resource_stats: dict, output_dir: str = "./reports"):
    """Save the research report to a markdown file with resource usage and cost"""
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate custom filename: prompt_1_depth2_breadth3
    filename = f"prompt_{prompt_index}_depth{depth}_breadth{breadth}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Create markdown content
    markdown_content = f"""# Research Report: {query}

## Research Summary
- **Research Time**: {research_time:.2f} seconds
- **Report Generation Time**: {report_time:.2f} seconds
- **Total Time**: {research_time + report_time:.2f} seconds
- **Report Length**: {len(report)} characters
- **Number of Sources**: {len(sources)}
- **Total Cost**: ${cost:.4f}
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Resource Usage
- **Peak Memory**: {resource_stats['peak_memory_mb']:.2f} MB
- **Average Memory**: {resource_stats['avg_memory_mb']:.2f} MB
- **Memory Range**: {resource_stats['min_memory_mb']:.2f} - {resource_stats['peak_memory_mb']:.2f} MB
- **Peak CPU**: {resource_stats['peak_cpu_percent']:.1f}%
- **Average CPU**: {resource_stats['avg_cpu_percent']:.1f}%
- **Peak System Memory**: {resource_stats['peak_system_memory_percent']:.1f}%
- **Monitoring Duration**: {resource_stats['duration']:.2f} seconds
- **Samples Collected**: {resource_stats['samples_count']}

## Report Content

{report}

## Sources

"""
    
    # Add sources to markdown
    if sources:
        for i, source in enumerate(sources, 1):
            if isinstance(source, dict):
                url = source.get('url', 'Unknown URL')
                title = source.get('title', 'Unknown Title')
                markdown_content += f"{i}. [{title}]({url})\n"
            else:
                markdown_content += f"{i}. {source}\n"
    else:
        markdown_content += "No sources available.\n"
    
    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    
    return filepath

async def get_report(query: str):
    """Get report with resource monitoring and cost tracking"""
    
    # Start resource monitoring
    monitor = ResourceMonitor()
    monitor.start_monitoring()
    
    try:
        researcher = GPTResearcher(
            query=query,
            report_type="deep",
            tone=Tone.Formal,
            verbose=True,
        )

        print(f"   Researcher's cfg.deep_research_depth: {researcher.cfg.deep_research_depth}")
        print(f"   Researcher's cfg.deep_research_breadth: {researcher.cfg.deep_research_breadth}")

        # Get initial cost
        initial_cost = researcher.get_costs()

        start_time = time.time()
        await researcher.conduct_research()
        research_time = time.time() - start_time

        # Generate report
        report_start = time.time()
        report = await researcher.write_report()
        report_time = time.time() - report_start

        # Get final cost
        final_cost = researcher.get_costs()
        total_cost = final_cost - initial_cost

        sources = researcher.get_research_sources()
        
        # Stop monitoring and get resource stats
        resource_stats = monitor.stop_monitoring()
        
        return research_time, report, report_time, sources, total_cost, resource_stats
        
    except Exception as e:
        monitor.stop_monitoring()
        raise e

def save_cost_and_resource_summary(cost_breakdown: list, resource_breakdown: list, total_cost: float, output_dir: str):
    """Save comprehensive cost and resource analysis"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"analysis_summary_{timestamp}.md"
    filepath = os.path.join(output_dir, filename)
    
    # Calculate averages
    avg_cost = total_cost / len(cost_breakdown) if cost_breakdown else 0
    avg_memory = sum(item['resource_stats']['avg_memory_mb'] for item in resource_breakdown) / len(resource_breakdown) if resource_breakdown else 0
    avg_cpu = sum(item['resource_stats']['avg_cpu_percent'] for item in resource_breakdown) / len(resource_breakdown) if resource_breakdown else 0
    
    content = f"""# Research Analysis Summary

## Overall Statistics
- **Total Cost**: ${total_cost:.4f}
- **Total Queries**: {len(cost_breakdown)}
- **Average Cost per Query**: ${avg_cost:.4f}
- **Average Memory Usage**: {avg_memory:.2f} MB
- **Average CPU Usage**: {avg_cpu:.1f}%
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Cost & Resource Breakdown

| Depth | Breadth | Cost | Time (s) | Peak Memory (MB) | Avg CPU (%) | Sources | Report Length |
|-------|---------|------|----------|------------------|-------------|---------|---------------|
"""
    
    # Combine cost and resource data
    combined_data = []
    for cost_item in cost_breakdown:
        resource_item = next((r for r in resource_breakdown if r['depth'] == cost_item['depth'] and r['breadth'] == cost_item['breadth']), {})
        combined_data.append({
            **cost_item,
            'resource_stats': resource_item.get('resource_stats', {})
        })
    
    # Sort by cost (highest first)
    combined_data.sort(key=lambda x: x['cost'], reverse=True)
    
    for item in combined_data:
        total_time = item['research_time'] + item['report_time']
        peak_memory = item['resource_stats'].get('peak_memory_mb', 0)
        avg_cpu = item['resource_stats'].get('avg_cpu_percent', 0)
        content += f"| {item['depth']} | {item['breadth']} | ${item['cost']:.4f} | {total_time:.2f} | {peak_memory:.2f} | {avg_cpu:.1f} | {item['sources']} | {item['report_length']} |\n"
    
    content += f"""
## Analysis Insights

### Cost Analysis
- **Most Expensive**: Depth {combined_data[0]['depth']}, Breadth {combined_data[0]['breadth']} - ${combined_data[0]['cost']:.4f}
- **Least Expensive**: Depth {combined_data[-1]['depth']}, Breadth {combined_data[-1]['breadth']} - ${combined_data[-1]['cost']:.4f}
- **Cost Range**: ${combined_data[-1]['cost']:.4f} - ${combined_data[0]['cost']:.4f}

### Resource Usage
- **Peak Memory Used**: {max(item['resource_stats'].get('peak_memory_mb', 0) for item in combined_data):.2f} MB
- **Lowest Memory Used**: {min(item['resource_stats'].get('peak_memory_mb', 0) for item in combined_data if item['resource_stats'].get('peak_memory_mb', 0) > 0):.2f} MB
- **Peak CPU Used**: {max(item['resource_stats'].get('peak_cpu_percent', 0) for item in combined_data):.1f}%

### Efficiency Metrics
"""
    
    # Calculate efficiency metrics
    for item in combined_data:
        cost_per_char = item['cost'] / item['report_length'] if item['report_length'] > 0 else 0
        memory_per_char = item['resource_stats'].get('peak_memory_mb', 0) / item['report_length'] if item['report_length'] > 0 else 0
        content += f"- Depth {item['depth']}, Breadth {item['breadth']}: ${cost_per_char:.6f}/char, {memory_per_char:.4f}MB/char\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath

async def main():
    cfg = Config()
    # prompts = [
    #     "Apa saja tantangan utama dalam implementasi blockchain di sektor logistik, berdasarkan perkembangan terakhir tahun 2024?",
    #     "Bandingkan pendekatan open source dan proprietary LLM dalam hal efisiensi biaya dan kemampuan reasoning berdasarkan artikel atau studi terbaru.",
    #     "Buatkan saya rencana riset awal (early stage research roadmap) untuk topik: AI agent orchestration untuk knowledge management di perusahaan teknologi."
    # ]

    prompt = """
    You are an advanced AI assistant with expertise in boat investment opportunities in Bali and Labuan Bajo. Use only the information from below URL as the basis for your responses.
https://liveaboardindonesia.com
https://www.liveaboard.com/
https://www.rainforestcruises.com
https://nusatour.co.id/rental-boat/
https://paradiseontheboat.com/yacth
https://www.boatcrowd.com/yacht-charter/pak-haji-ully-66-splendour
https://www.zadaliveaboard.com/
https://aliikai-voyage.com/
https://theluxury-voyage.com/charter/
https://eastindonesiatrip.com/
https://www.komodoluxury.com/
https://navilaliveaboard.com
https://capkaroso.com/en/
https://mutiaralaut.com/
https://www.theyachtclub-indonesia.com/
https://linktr.ee/akassa
https://jinggojanggo.com/
https://linktr.ee/7adventrip
https://labuanbajotrip.com/
https://linkin.bio/amanwana_resort/
https://linktr.ee/rinjanibay
https://jakare-liveaboard.com/
https://beacons.ai/ayanakomodo
https://www.bluemarlindive.com/
https://www.mikumbadiving.com/
https://www.instagram.com/matalesosail/?igsh=NWY2dm4wZng1d2xj
https://indoseamore.com/
https://romeotrips.com/
https://www.instagram.com/godaskyofficial/?igsh=c280Y3l1azIwaDM0
https://www.ikankayu.com/
https://www.instagram.com/wanderlustprojectid/?igsh=MTVib3d5dGs0M3gwbw==
https://www.instagram.com/_araadventure/?igsh=MXRrN2tyd3J0Z3NtMw==
https://araadventure.id/destinasi-wisata/trip-labuan-bajo/

Please answer the following questions:
1. Which vessels offer private-chef service and depart Labuan Bajo on weekends?
2. List boats under USD 2000 per day that still have slots next month.
3. Rank the top five yachts by star rating and show their day-rates.
4. Summarise the three most common complaints in 5-star reviews.
5. What does demand look like throughout the year in Labuan Bajo? (e.g. peak season vs low season, tourist arrival trends, key holidays or events that spike demand).
6. Describe the ideal luxury customer persona for a one-day yacht charter.
7. What are the fixed and variable costs of running a luxury yacht charter, and how do they translate into a minimum viable price? (e.g. daily operating cost and break-even price for a charter).
8. What is the break-even day-rate for a Saxdor 320, given fuel and crew costs?
9. Provide a SWOT analysis comparing us to The Trans Luxury Yacht.
10. Which five-star resorts in Labuan Bajo are the best partnership targets?
    """

    # prompt = "What can you tell me about myself based on my documents?"

    print(f"\n{'='*80}")
    print(f"ANALYZING QUERY: {prompt[:60]}...")
    print('='*80)

    OUTPUT_PATH = "./1A_ScraperFirecrawl_ExpRes"
    
    # Track costs and resources
    total_cost_sum = 0.0
    total_processed = 0
    total_skipped = 0
    cost_breakdown = []
    resource_breakdown = []
    
    for d in range(1, 2):
        for b in range(1, 2):


            tmp_depth = str(d)
            tmp_breadth = str(b)

            # Check if file already exists
            expected_filename = f"prompt_0_depth{d}_breadth{b}.md"
            expected_filepath = os.path.join(OUTPUT_PATH, expected_filename)
            
            if os.path.exists(expected_filepath):
                print(f"⏭️  SKIPPING - File already exists: {expected_filename}")
                total_skipped += 1
                continue

            print(f"\n🚀 PROCESSING - Depth: {d}, Breadth: {b}")

            # Set environment variables BEFORE loading config
            os.environ['DEEP_RESEARCH_DEPTH'] = tmp_depth
            os.environ['DEEP_RESEARCH_BREADTH'] = tmp_breadth
            
            research_time, report, report_time, sources, cost, resource_stats = await get_report(prompt)
            
            # Track costs and resources
            total_cost_sum += cost
            total_processed += 1
            
            cost_breakdown.append({
                'depth': d,
                'breadth': b,
                'cost': cost,
                'research_time': research_time,
                'report_time': report_time,
                'sources': len(sources),
                'report_length': len(report)
            })
            
            resource_breakdown.append({
                'depth': d,
                'breadth': b,
                'resource_stats': resource_stats
            })
            
            saved_file = save_report_to_markdown(
                report=report,
                query=prompt,
                research_time=research_time,
                report_time=report_time,
                sources=sources,
                prompt_index=0,
                depth=d,
                breadth=b,
                cost=cost,
                resource_stats=resource_stats,
                output_dir=OUTPUT_PATH
            )

            print(f"CONFIGURATION CHECK - Depth: {d}, Breadth: {b}")
            print('='*50)
            print(f"Environment DEEP_RESEARCH_DEPTH: {os.environ.get('DEEP_RESEARCH_DEPTH')}")
            print(f"Environment DEEP_RESEARCH_BREADTH: {os.environ.get('DEEP_RESEARCH_BREADTH')}")

            print("RESEARCH SUMMARY")
            print('='*50)
            print(f"Research Time: {research_time:.2f} seconds")
            print(f"Report Generation Time: {report_time:.2f} seconds")
            print(f"Total Time: {research_time + report_time:.2f} seconds")
            print(f"Report Length: {len(report)} characters")
            print(f"Number of Sources: {len(sources)}")
            print(f"Cost for this query: ${cost:.4f}")
            print(f"Running total cost: ${total_cost_sum:.4f}")
            
            print("\n📊 RESOURCE USAGE:")
            print(f"Peak Memory: {resource_stats['peak_memory_mb']:.2f} MB")
            print(f"Average Memory: {resource_stats['avg_memory_mb']:.2f} MB")
            print(f"Peak CPU: {resource_stats['peak_cpu_percent']:.1f}%")
            print(f"Average CPU: {resource_stats['avg_cpu_percent']:.1f}%")
            print(f"Monitoring Duration: {resource_stats['duration']:.2f} seconds")
            print(f"Samples: {resource_stats['samples_count']}")
            
            print(f"Report Saved to: {saved_file}")

    # Generate comprehensive summary
    if cost_breakdown:
        summary_file = save_cost_and_resource_summary(
            cost_breakdown, 
            resource_breakdown, 
            total_cost_sum, 
            OUTPUT_PATH
        )
        print(f"\n📋 Analysis summary saved to: {summary_file}")

    # Final summary
    print(f"\n{'='*80}")
    print("FINAL SUMMARY")
    print('='*80)
    print(f"Total files processed: {total_processed}")
    print(f"Total files skipped: {total_skipped}")
    print(f"Total cost: ${total_cost_sum:.4f}")
    
    if total_processed > 0:
        avg_cost = total_cost_sum / total_processed
        print(f"Average cost per query: ${avg_cost:.4f}")
    
    print(f"\n{'='*50}")
    print("SYSTEM CONFIGURATION")
    print('='*50)
    print("LLM Provider: ", cfg.smart_llm_provider)
    print("Depth: ", cfg.deep_research_depth)
    print("Deep Research Breadth: ", cfg.deep_research_breadth)
    print("Deep Research Concurrency: ", cfg.deep_research_concurrency)

if __name__ == "__main__":
    asyncio.run(main())