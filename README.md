# Thống kê XSMN

Trang tĩnh thống kê xổ số Miền Nam (21 đài) và đưa ra số tham khảo cho kỳ quay tới,
tự cập nhật mỗi ngày bằng GitHub Actions và đăng trên GitHub Pages.

> Xổ số là ngẫu nhiên. Trang hiện công khai tỉ lệ trúng thực tế của mọi cách gợi ý
> (thử lại trên toàn bộ lịch sử): tất cả đều quanh mức may rủi. Đây là công cụ thống kê, giải trí.

## Cấu trúc

| File | Việc |
|---|---|
| `scrape.py` | Tải kết quả theo ngày từ minhngoc.net.vn → `data/<đài>.csv` |
| `build.py` | Thống kê, gợi ý, backtest → `site/data/*.json` |
| `site/` | Trang web (HTML/CSS/JS thuần, không cần build) |
| `analyze.py` | Báo cáo thống kê dạng chữ cho một đài: `python analyze.py data/vinh-long.csv` |
| `.github/workflows/update.yml` | Chạy 16:50 và 18:30 giờ VN mỗi ngày: tải → commit dữ liệu → build → đăng Pages |

## Chạy trên máy

```bash
python scrape.py                     # cập nhật kỳ mới
python scrape.py --since 2008-01-01  # tải lại toàn bộ (~1 giờ)
python build.py
python -m http.server -d site 8000   # mở http://localhost:8000
```

## Cách tính gợi ý (giải 8, mỗi bộ 6 số)

- **Số nóng**: 6 số về nhiều nhất từ trước tới kỳ đó.
- **Lô gan**: 6 số lâu chưa về nhất.
- **Ngẫu nhiên**: rút thăm, cố định theo đài + ngày.
- **Đặc biệt**: chữ số về nhiều nhất ở từng vị trí, và một số rút thăm.

Backtest là walk-forward: gợi ý cho mỗi kỳ trong quá khứ chỉ dùng dữ liệu trước kỳ đó.
