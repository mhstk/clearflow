#!/usr/bin/env python3
"""
Test script for AI categorization feature.

Tests the batch categorization endpoint with sample transactions.
"""

import requests
import json
from rich.console import Console
from rich.table import Table
from rich import print as rprint

BASE_URL = "http://localhost:8000/api/v1"
console = Console()


def test_categorization():
    """Test the AI categorization feature."""

    console.print("\n[bold cyan]🤖 Testing AI Categorization Feature[/bold cyan]\n")

    # Step 1: Get some uncategorized transactions
    console.print("[yellow]Step 1:[/yellow] Fetching uncategorized transactions...\n")

    try:
        response = requests.get(
            f"{BASE_URL}/transactions/view",
            params={
                "page_size": 5,
                "page": 1
            }
        )
        response.raise_for_status()
        data = response.json()

        transactions = data.get("rows", [])

        if not transactions:
            console.print("[red]❌ No transactions found! Please upload a CSV first.[/red]")
            console.print("\n[yellow]Upload CSV with:[/yellow]")
            console.print("curl -X POST 'http://localhost:8000/api/v1/transactions/upload_csv' \\")
            console.print("  -F 'file=@sample_statement.csv'\n")
            return

        # Display transactions
        table = Table(title="Transactions to Categorize")
        table.add_column("ID", style="cyan")
        table.add_column("Date", style="green")
        table.add_column("Merchant", style="yellow")
        table.add_column("Amount", style="magenta")
        table.add_column("Current Category", style="blue")

        transaction_ids = []
        for txn in transactions[:5]:
            table.add_row(
                str(txn["id"]),
                txn["date"],
                txn["description_raw"][:40],
                f"${abs(txn['amount']):.2f}",
                txn["category"]
            )
            transaction_ids.append(txn["id"])

        console.print(table)
        console.print()

    except requests.exceptions.ConnectionError:
        console.print("[red]❌ Error: API server is not running![/red]")
        console.print("[yellow]Start the server with:[/yellow] python run.py\n")
        return
    except Exception as e:
        console.print(f"[red]❌ Error fetching transactions: {e}[/red]\n")
        return

    # Step 2: Get valid categories
    console.print("[yellow]Step 2:[/yellow] Fetching valid categories...\n")

    try:
        response = requests.get(f"{BASE_URL}/ai/categories")
        response.raise_for_status()
        categories = response.json()

        console.print("[green]✅ Valid Categories:[/green]")
        console.print(", ".join(categories))
        console.print()

    except Exception as e:
        console.print(f"[red]❌ Error fetching categories: {e}[/red]\n")
        return

    # Step 3: Categorize transactions with AI
    console.print("[yellow]Step 3:[/yellow] Calling AI categorization endpoint...\n")

    try:
        response = requests.post(
            f"{BASE_URL}/ai/categorize_batch",
            json={
                "transaction_ids": transaction_ids,
                "auto_apply": False  # Preview mode
            }
        )
        response.raise_for_status()
        result = response.json()

        # Display results
        console.print(f"[green]✅ AI Categorization Complete![/green]\n")
        console.print(f"[cyan]Total Processed:[/cyan] {result['total_processed']}")
        console.print(f"[green]Successful:[/green] {result['successful']}")
        console.print(f"[red]Failed:[/red] {result['failed']}")
        console.print()

        # Display detailed results
        results_table = Table(title="AI Categorization Results")
        results_table.add_column("Transaction ID", style="cyan")
        results_table.add_column("AI Category", style="green", no_wrap=True)
        results_table.add_column("Note", style="yellow")
        results_table.add_column("Confidence", style="magenta", no_wrap=True)
        results_table.add_column("Applied", style="blue", no_wrap=True)
        results_table.add_column("Error", style="red")

        for res in result["results"]:
            results_table.add_row(
                str(res["transaction_id"]),
                res["category"],
                res["note"][:40] if len(res["note"]) > 40 else res["note"],
                res["confidence"],
                "✅" if res["applied"] else "❌",
                res.get("error", "") or "—"
            )

        console.print(results_table)
        console.print()

        # Print raw JSON for inspection
        console.print("[yellow]Raw JSON Response:[/yellow]")
        console.print(json.dumps(result, indent=2))
        console.print()

        # Summary by confidence
        confidence_counts = {}
        for res in result["results"]:
            conf = res["confidence"]
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1

        console.print("[cyan]Confidence Distribution:[/cyan]")
        for conf, count in confidence_counts.items():
            console.print(f"  {conf.capitalize()}: {count}")
        console.print()

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 500:
            error_detail = e.response.json().get("detail", "Unknown error")

            if "No API key" in error_detail or "OPENROUTER_API_KEY" in error_detail:
                console.print("[red]❌ OpenRouter API Key Not Configured[/red]\n")
                console.print("[yellow]To enable AI categorization:[/yellow]")
                console.print("1. Get a free API key from: https://openrouter.ai/")
                console.print("2. Add to .env file:")
                console.print("   OPENROUTER_API_KEY=your_key_here")
                console.print("3. Restart the server")
                console.print()
                console.print("[blue]ℹ️  The system will return stub data without an API key.[/blue]\n")
            else:
                console.print(f"[red]❌ Server Error: {error_detail}[/red]\n")
        else:
            console.print(f"[red]❌ HTTP Error: {e}[/red]\n")
    except Exception as e:
        console.print(f"[red]❌ Error during categorization: {e}[/red]\n")
        import traceback
        traceback.print_exc()

    # Step 4: Test with auto_apply=True
    console.print("\n[yellow]Step 4:[/yellow] Testing with auto_apply=True...\n")

    try:
        console.print("[yellow]⚠️  This will actually modify the transactions in the database.[/yellow]")
        console.print("[yellow]Press Enter to continue or Ctrl+C to cancel...[/yellow]")
        input()

        response = requests.post(
            f"{BASE_URL}/ai/categorize_batch",
            json={
                "transaction_ids": transaction_ids,
                "auto_apply": True  # Actually apply to database
            }
        )
        response.raise_for_status()
        result = response.json()

        console.print(f"\n[green]✅ Categories Applied to Database![/green]\n")
        console.print(f"Successful: {result['successful']}/{result['total_processed']}")
        console.print()

        # Verify by fetching transactions again
        response = requests.get(
            f"{BASE_URL}/transactions/view",
            params={"page_size": 5}
        )
        transactions = response.json().get("rows", [])

        verify_table = Table(title="Updated Transactions")
        verify_table.add_column("ID", style="cyan")
        verify_table.add_column("Merchant", style="yellow")
        verify_table.add_column("New Category", style="green")
        verify_table.add_column("Note", style="magenta")

        for txn in transactions[:5]:
            verify_table.add_row(
                str(txn["id"]),
                txn["description_raw"][:30],
                txn["category"],
                txn.get("note_user", "—") or "—"
            )

        console.print(verify_table)
        console.print()

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Skipped auto_apply test.[/yellow]\n")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]\n")


def main():
    """Main function."""
    try:
        test_categorization()

        console.print("[bold green]✅ Test Complete![/bold green]\n")
        console.print("[cyan]Next Steps:[/cyan]")
        console.print("1. Check the AI categorization results above")
        console.print("2. Adjust prompts in app/prompts/categorization.py if needed")
        console.print("3. Modify VALID_CATEGORIES in app/services/auto_categorization.py")
        console.print("4. Upload more transactions to test with")
        console.print()

    except KeyboardInterrupt:
        console.print("\n\n[yellow]Test cancelled by user.[/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]❌ Test failed: {e}[/red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if rich is installed
    try:
        import rich
    except ImportError:
        print("⚠️  Installing 'rich' for better output formatting...")
        import subprocess
        subprocess.check_call(["pip", "install", "rich"])
        print("✅ 'rich' installed! Rerun the script.\n")
        exit(0)

    main()
