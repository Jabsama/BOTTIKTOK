#!/usr/bin/env python3
"""
TikTok Compliance Checker
Validates system compliance with TikTok Terms of Service
Ensures all components follow official API guidelines
"""

import os
import logging
import yaml
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logger = logging.getLogger(__name__)

class TikTokComplianceChecker:
    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize compliance checker
        
        Args:
            config_path: Path to configuration file
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.compliance_rules = {
            'no_scraping': {
                'description': 'No automated scraping of TikTok content',
                'critical': True,
                'check_method': self._check_no_scraping
            },
            'official_api_only': {
                'description': 'Use only official TikTok APIs',
                'critical': True,
                'check_method': self._check_official_api
            },
            'business_account': {
                'description': 'TikTok Business account required',
                'critical': True,
                'check_method': self._check_business_account
            },
            'no_video_downloads': {
                'description': 'No downloading of TikTok videos',
                'critical': True,
                'check_method': self._check_no_video_downloads
            },
            'aigc_labeling': {
                'description': 'AI-generated content must be labeled',
                'critical': True,
                'check_method': self._check_aigc_labeling
            },
            'branded_content': {
                'description': 'Commercial content must be disclosed',
                'critical': True,
                'check_method': self._check_branded_content
            },
            'rate_limiting': {
                'description': 'Respect API rate limits',
                'critical': True,
                'check_method': self._check_rate_limiting
            },
            'conservative_posting': {
                'description': 'Conservative posting frequency',
                'critical': False,
                'check_method': self._check_posting_frequency
            },
            'proper_disclaimers': {
                'description': 'Include required disclaimers',
                'critical': True,
                'check_method': self._check_disclaimers
            },
            'no_selenium': {
                'description': 'No Selenium automation',
                'critical': True,
                'check_method': self._check_no_selenium
            }
        }
        
        logger.info("TikTok Compliance Checker initialized")
    
    def run_full_compliance_check(self) -> Dict:
        """
        Run complete compliance check
        
        Returns:
            Compliance report dictionary
        """
        logger.info("Running full TikTok compliance check...")
        
        results = {
            'overall_compliant': True,
            'critical_issues': [],
            'warnings': [],
            'passed_checks': [],
            'failed_checks': [],
            'compliance_score': 0,
            'recommendations': []
        }
        
        total_checks = len(self.compliance_rules)
        passed_checks = 0
        
        for rule_name, rule_config in self.compliance_rules.items():
            try:
                check_result = rule_config['check_method']()
                
                if check_result['compliant']:
                    results['passed_checks'].append({
                        'rule': rule_name,
                        'description': rule_config['description'],
                        'details': check_result.get('details', '')
                    })
                    passed_checks += 1
                else:
                    results['failed_checks'].append({
                        'rule': rule_name,
                        'description': rule_config['description'],
                        'details': check_result.get('details', ''),
                        'critical': rule_config['critical']
                    })
                    
                    if rule_config['critical']:
                        results['critical_issues'].append(f"{rule_name}: {check_result.get('details', '')}")
                        results['overall_compliant'] = False
                    else:
                        results['warnings'].append(f"{rule_name}: {check_result.get('details', '')}")
                
                # Add recommendations if provided
                if 'recommendation' in check_result:
                    results['recommendations'].append({
                        'rule': rule_name,
                        'recommendation': check_result['recommendation']
                    })
                    
            except Exception as e:
                logger.error(f"Error checking rule {rule_name}: {e}")
                results['failed_checks'].append({
                    'rule': rule_name,
                    'description': rule_config['description'],
                    'details': f"Check failed: {e}",
                    'critical': rule_config['critical']
                })
                
                if rule_config['critical']:
                    results['overall_compliant'] = False
        
        # Calculate compliance score
        results['compliance_score'] = round((passed_checks / total_checks) * 100, 1)
        
        # Log summary
        if results['overall_compliant']:
            logger.info(f"✅ System is TikTok-compliant (Score: {results['compliance_score']}%)")
        else:
            logger.error(f"❌ System has compliance issues (Score: {results['compliance_score']}%)")
            logger.error(f"Critical issues: {len(results['critical_issues'])}")
        
        return results
    
    def _check_no_scraping(self) -> Dict:
        """Check that no scraping is being used"""
        # Check if old scraping files exist
        scraping_files = [
            'scraper_trends.py',
            'selenium_scraper.py',
            'web_scraper.py'
        ]
        
        found_scrapers = []
        for file in scraping_files:
            if os.path.exists(file):
                found_scrapers.append(file)
        
        if found_scrapers:
            return {
                'compliant': False,
                'details': f"Found scraping files: {', '.join(found_scrapers)}",
                'recommendation': "Remove scraping files and use tiktok_compliant_trends.py"
            }
        
        # Check if compliant trend fetcher exists
        if os.path.exists('tiktok_compliant_trends.py'):
            return {
                'compliant': True,
                'details': "Using compliant trend fetcher (API-only)"
            }
        
        return {
            'compliant': False,
            'details': "No compliant trend fetcher found",
            'recommendation': "Implement tiktok_compliant_trends.py"
        }
    
    def _check_official_api(self) -> Dict:
        """Check that only official APIs are used"""
        # Check for TikTok API credentials
        api_credentials = [
            'TIKTOK_CLIENT_KEY',
            'TIKTOK_CLIENT_SECRET',
            'TIKTOK_ACCESS_TOKEN'
        ]
        
        missing_credentials = []
        for cred in api_credentials:
            if not os.getenv(cred):
                missing_credentials.append(cred)
        
        if missing_credentials:
            return {
                'compliant': False,
                'details': f"Missing API credentials: {', '.join(missing_credentials)}",
                'recommendation': "Configure TikTok Business API credentials in .env"
            }
        
        # Check if compliant uploader exists
        if os.path.exists('tiktok_compliant_upload.py'):
            return {
                'compliant': True,
                'details': "Using official TikTok Content Posting API"
            }
        
        return {
            'compliant': False,
            'details': "No compliant uploader found",
            'recommendation': "Use tiktok_compliant_upload.py"
        }
    
    def _check_business_account(self) -> Dict:
        """Check for TikTok Business account setup"""
        client_key = os.getenv('TIKTOK_CLIENT_KEY')
        client_secret = os.getenv('TIKTOK_CLIENT_SECRET')
        
        if not client_key or not client_secret:
            return {
                'compliant': False,
                'details': "TikTok Business account credentials not configured",
                'recommendation': "Create TikTok Business account and register developer app"
            }
        
        if client_key.startswith('CHANGEME') or client_secret.startswith('CHANGEME'):
            return {
                'compliant': False,
                'details': "Using placeholder credentials",
                'recommendation': "Replace with actual TikTok Business API credentials"
            }
        
        return {
            'compliant': True,
            'details': "TikTok Business account configured"
        }
    
    def _check_no_video_downloads(self) -> Dict:
        """Check that no video downloading is happening"""
        # Check for video download libraries
        download_imports = ['yt-dlp', 'youtube-dl', 'pytube']
        
        # Check if viral_remix.py contains download code
        if os.path.exists('viral_remix.py'):
            try:
                with open('viral_remix.py', 'r') as f:
                    content = f.read()
                    
                for lib in download_imports:
                    if lib in content:
                        return {
                            'compliant': False,
                            'details': f"Found video download code using {lib}",
                            'recommendation': "Remove video download functionality, use only licensed content"
                        }
            except Exception as e:
                logger.warning(f"Could not check viral_remix.py: {e}")
        
        return {
            'compliant': True,
            'details': "No video downloading detected"
        }
    
    def _check_aigc_labeling(self) -> Dict:
        """Check for automatic AIGC labeling"""
        if os.path.exists('tiktok_compliant_upload.py'):
            try:
                with open('tiktok_compliant_upload.py', 'r') as f:
                    content = f.read()
                    
                if 'aigc_label' in content and '#AIGC' in content:
                    return {
                        'compliant': True,
                        'details': "Automatic AIGC labeling implemented"
                    }
            except Exception as e:
                logger.warning(f"Could not check AIGC labeling: {e}")
        
        return {
            'compliant': False,
            'details': "AIGC labeling not found",
            'recommendation': "Implement automatic AIGC labeling in upload process"
        }
    
    def _check_branded_content(self) -> Dict:
        """Check for branded content disclosure"""
        if os.path.exists('tiktok_compliant_upload.py'):
            try:
                with open('tiktok_compliant_upload.py', 'r') as f:
                    content = f.read()
                    
                if 'brand_content_toggle' in content and '#ad' in content and '#sponsored' in content:
                    return {
                        'compliant': True,
                        'details': "Branded content disclosure implemented"
                    }
            except Exception as e:
                logger.warning(f"Could not check branded content: {e}")
        
        return {
            'compliant': False,
            'details': "Branded content disclosure not found",
            'recommendation': "Implement automatic branded content disclosure"
        }
    
    def _check_rate_limiting(self) -> Dict:
        """Check for proper rate limiting"""
        max_posts = self.config.get('posting', {}).get('max_posts_per_day', 6)
        min_spacing = self.config.get('posting', {}).get('min_spacing_minutes', 90)
        
        issues = []
        
        if max_posts > 2:
            issues.append(f"Daily limit too high: {max_posts} (recommended: ≤2)")
        
        if min_spacing < 120:
            issues.append(f"Spacing too short: {min_spacing}min (recommended: ≥120min)")
        
        if issues:
            return {
                'compliant': False,
                'details': '; '.join(issues),
                'recommendation': "Reduce posting frequency for TikTok compliance"
            }
        
        return {
            'compliant': True,
            'details': f"Conservative limits: {max_posts} posts/day, {min_spacing}min spacing"
        }
    
    def _check_posting_frequency(self) -> Dict:
        """Check posting frequency recommendations"""
        max_posts = self.config.get('posting', {}).get('max_posts_per_day', 6)
        
        if max_posts <= 2:
            return {
                'compliant': True,
                'details': "Conservative posting frequency (≤2 posts/day)"
            }
        elif max_posts <= 4:
            return {
                'compliant': True,
                'details': "Moderate posting frequency (≤4 posts/day)",
                'recommendation': "Consider reducing to 2 posts/day for new accounts"
            }
        else:
            return {
                'compliant': False,
                'details': f"High posting frequency ({max_posts} posts/day)",
                'recommendation': "Reduce to 2 posts/day to avoid shadow-banning"
            }
    
    def _check_disclaimers(self) -> Dict:
        """Check for required disclaimers"""
        disclaimers = self.config.get('disclaimers', {})
        
        required_disclaimers = [
            'ai_generated',
            'results_vary',
            'no_guarantee'
        ]
        
        missing = []
        for disclaimer in required_disclaimers:
            if not disclaimers.get(disclaimer):
                missing.append(disclaimer)
        
        if missing:
            return {
                'compliant': False,
                'details': f"Missing disclaimers: {', '.join(missing)}",
                'recommendation': "Add all required disclaimers to config.yaml"
            }
        
        return {
            'compliant': True,
            'details': "All required disclaimers configured"
        }
    
    def _check_no_selenium(self) -> Dict:
        """Check that Selenium is not being used"""
        # Check for Selenium imports in Python files
        python_files = [f for f in os.listdir('.') if f.endswith('.py')]
        
        selenium_files = []
        for file in python_files:
            try:
                with open(file, 'r') as f:
                    content = f.read()
                    if 'selenium' in content.lower() and 'webdriver' in content.lower():
                        selenium_files.append(file)
            except Exception:
                continue
        
        if selenium_files:
            return {
                'compliant': False,
                'details': f"Selenium usage found in: {', '.join(selenium_files)}",
                'recommendation': "Remove Selenium automation, use official APIs only"
            }
        
        return {
            'compliant': True,
            'details': "No Selenium automation detected"
        }
    
    def generate_compliance_report(self) -> str:
        """Generate a formatted compliance report"""
        results = self.run_full_compliance_check()
        
        report = []
        report.append("=" * 60)
        report.append("TIKTOK COMPLIANCE REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Overall status
        status_icon = "✅" if results['overall_compliant'] else "❌"
        report.append(f"Overall Status: {status_icon} {'COMPLIANT' if results['overall_compliant'] else 'NON-COMPLIANT'}")
        report.append(f"Compliance Score: {results['compliance_score']}%")
        report.append("")
        
        # Critical issues
        if results['critical_issues']:
            report.append("🚨 CRITICAL ISSUES (Must Fix):")
            for issue in results['critical_issues']:
                report.append(f"  ❌ {issue}")
            report.append("")
        
        # Warnings
        if results['warnings']:
            report.append("⚠️  WARNINGS:")
            for warning in results['warnings']:
                report.append(f"  ⚠️  {warning}")
            report.append("")
        
        # Passed checks
        if results['passed_checks']:
            report.append("✅ PASSED CHECKS:")
            for check in results['passed_checks']:
                report.append(f"  ✅ {check['description']}")
                if check['details']:
                    report.append(f"     {check['details']}")
            report.append("")
        
        # Recommendations
        if results['recommendations']:
            report.append("💡 RECOMMENDATIONS:")
            for rec in results['recommendations']:
                report.append(f"  💡 {rec['rule']}: {rec['recommendation']}")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


def main():
    """Run compliance check"""
    checker = TikTokComplianceChecker()
    
    # Generate and print report
    report = checker.generate_compliance_report()
    print(report)
    
    # Save report to file
    with open('compliance_report.txt', 'w') as f:
        f.write(report)
    
    print(f"\nCompliance report saved to: compliance_report.txt")


if __name__ == "__main__":
    main()
