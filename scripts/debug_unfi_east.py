"""Helper script to parse UNFI East sample PDFs for debugging."""

import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

load_dotenv(override=True)

from parsers.unfi_east_parser import UNFIEastParser
from utils.mapping_utils import MappingUtils


def parse_file(path: Path):
    parser = UNFIEastParser(MappingUtils(use_database=True))
    data = path.read_bytes()
    print(f"\n=== Parsing {path.name} ===")
    try:
        orders = parser.parse(data, 'pdf', path.name)
        if not orders:
            print("No orders parsed.")
        else:
            print(f"Parsed {len(orders)} orders.")
            for idx, order in enumerate(orders, 1):
                print(f"Order {idx}: {order.get('order_number')} with {order.get('item_number')}")
    except Exception as exc:
        print(f"Error parsing {path.name}: {exc}")
        raise


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_unfi_east.py <pdf_path>")
        sys.exit(1)
    pdf_path = Path(sys.argv[1])
    parse_file(pdf_path)

