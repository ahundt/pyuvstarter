#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Naïve Data Processor - Testing Unicode filename handling.
This module demonstrates Unicode characters in filename and content.
"""

import os
import sys
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Union


class naïveDataProcessor:
    """A class with Unicode characters in name for testing."""

    def __init__(self, résumé_data: str = ""):
        self.résumé_data = résumé_data
        self.created_at = datetime.now()
        self.encoding_errors = []

    def process_french_names(self, names: List[str]) -> List[str]:
        """Process French names with accents."""
        processed = []
        for name in names:
            # Common French names with accents
            normalized = name.replace('é', 'e').replace('è', 'e').replace('ê', 'e')
            normalized = normalized.replace('à', 'a').replace('â', 'a').replace('ç', 'c')
            processed.append(normalized)
        return processed

    def process_chinese_data(self, data: Dict[str, str]) -> Dict[str, str]:
        """Process Chinese characters and data."""
        result = {}
        for key, value in data.items():
            # Handle Chinese characters (数据处理器)
            if any(ord(char) > 127 for char in value):
                result[key] = f"chinese_data_{len(value)}"
            else:
                result[key] = value
        return result

    def process_emoji_text(self, text: str) -> str:
        """Process text containing emoji characters."""
        # Remove emoji but keep the meaning
        emoji_map = {
            '😀': 'happy',
            '😎': 'cool',
            '🚀': 'rocket',
            '💡': 'idea',
            '⚡': 'lightning'
        }

        result = text
        for emoji, meaning in emoji_map.items():
            result = result.replace(emoji, f"[{meaning}]")

        return result

    def save_to_file(self, filename: str) -> bool:
        """Save data to file with Unicode filename support."""
        try:
            # Test various Unicode filenames
            unicode_filenames = [
                "naïve_output.json",
                "résumé_data.csv",
                "数据处理器.txt",
                "café_results.json",
                "emoji_test_😀😎🚀.txt"
            ]

            for unicode_name in unicode_filenames:
                filepath = os.path.join(os.path.dirname(filename), unicode_name)

                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump({
                        'résumé': self.résumé_data,
                        'timestamp': self.created_at.isoformat(),
                        'french_names': self.process_french_names(['André', 'François', 'Nicolas']),
                        'chinese_data': self.process_chinese_data({'姓名': '张三', '年龄': '25'}),
                        'emoji_text': self.process_emoji_text('Hello 😀 world 🚀!')
                    }, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            self.encoding_errors.append(str(e))
            return False


def main():
    """Main function demonstrating Unicode handling."""
    processor = naïveDataProcessor("Test résumé data")

    # Test Unicode filename handling
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Create test data with Unicode
    test_names = ['José', 'François', 'André', 'Sébastien']
    processed_names = processor.process_french_names(test_names)

    chinese_test = {'姓名': '李明', '城市': '北京', '职业': '工程师'}
    processed_chinese = processor.process_chinese_data(chinese_test)

    emoji_test = 'Processing data 😊 with emoji 🚀 and symbols ⚡'
    processed_emoji = processor.process_emoji_text(emoji_test)

    # Test file saving with Unicode filename
    output_file = os.path.join(current_dir, "naïve_output.json")
    success = processor.save_to_file(output_file)

    print(f"Unicode processing completed: {success}")
    print(f"Processed names: {processed_names}")
    print(f"Processed Chinese: {processed_chinese}")
    print(f"Processed emoji: {processed_emoji}")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)