"""
Точка входу для ДОСЛІДЖЕННЯ (без бота): повний конвеєр методики.

  1) довантаження історії курсів у БД;
  2) порівняння методів (walk-forward): MAE / RMSE / MAPE / точність напрямку;
  3) побудова графіків у папку charts/.

Запуск:  python main.py
Бот + міні-застосунок:  python run.py
"""

from charts import (plot_forecast_comparison, plot_mape_all_assets,
                    plot_methods_metrics_bar, plot_price_history)
from collector import backfill_history
from config import ALL_TICKERS, CHARTS_DIR
from database import init_db
from evaluation import evaluate_methods_on_ticker, print_comparison_table


def main():
    init_db()
    backfill_history()  # повторний запуск дублікатів не створює

    all_results = {}
    for ticker in ALL_TICKERS:
        print(f"\n=== Порівняння методів для {ticker} ===")
        results = evaluate_methods_on_ticker(ticker)
        all_results[ticker] = results
        if results:
            print_comparison_table(results)

    print("\n=== Побудова графіків ===")
    for ticker in ALL_TICKERS:
        plot_price_history(ticker)
        plot_forecast_comparison(ticker)
        plot_methods_metrics_bar(all_results[ticker], ticker)
    plot_mape_all_assets(all_results)

    print(f"\nГотово! Графіки збережено у папці {CHARTS_DIR}")


if __name__ == "__main__":
    main()
