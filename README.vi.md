# All Skills Library

Đây là thư viện skill hợp nhất, có truy vết nguồn, dành cho các tác vụ AI,
lập trình, bảo mật, dữ liệu, vận hành, kinh doanh, marketing, thiết kế, tài liệu,
nghiên cứu và công việc văn phòng.

Repo hiện có **2.706 skill canonical**, được chia thành **18 nhóm công việc**.
Mỗi skill chỉ tồn tại một bản cài đặt trong `skills/`; `collections/` chỉ là mục
lục được sinh tự động, nhờ đó không phát sinh các bản sao lệch nhau.

## Bắt đầu nhanh

- Xem theo nhóm công việc: [collections/README.md](collections/README.md)
- Xem toàn bộ catalog: [CATALOG.md](CATALOG.md)
- Dùng registry JSON: [catalog/skills.json](catalog/skills.json)
- Xem báo cáo chất lượng: [catalog/validation-report.json](catalog/validation-report.json)
- Tạo skill mới: [templates/SKILL.md](templates/SKILL.md)

## Cấu trúc

```text
skills/                 Nguồn canonical, mỗi skill một ID duy nhất
collections/            Mục lục theo 18 nhóm công việc
catalog/                Registry, thống kê và báo cáo kiểm tra
config/                 Taxonomy và chính sách import nguồn chính thức
docs/                   Kiến trúc, đóng góp và an toàn
spec/                   Đặc tả Agent Skills
templates/              Mẫu tạo skill
tools/repo_skills.py    Công cụ đồng bộ metadata, build catalog và validate
sources/                Snapshot nguồn cục bộ, không đưa vào Git
```

## Kiểm tra repo

```bash
python -m pip install -r requirements.txt
python tools/repo_skills.py all
```

Hoặc dùng npm:

```bash
npm run check
```

Bộ kiểm tra chặn lỗi cấu trúc như frontmatter hỏng, ID trùng, tên folder sai,
risk không hợp lệ và link nội bộ thoát khỏi repo. Các thiếu sót biên tập như chưa
có mục `Limitations` được ghi thành cảnh báo để có thể xử lý dần mà không làm hỏng
toàn bộ catalog.

## Nguyên tắc chọn bản canonical

- Chỉ giữ một bản cài đặt cho mỗi ID trong `skills/`.
- Ưu tiên nguồn chính thức cho workflow gắn với nhà cung cấp.
- Ưu tiên Anthropic cho Claude, creative và xử lý tài liệu chuyên sâu.
- Ưu tiên OpenAI cho Codex, sản phẩm OpenAI, plugin và tích hợp chính thức.
- Giữ bản bị thay thế trong `sources/replaced-canonical/` để đối chiếu.
- Giữ nguyên file license đi kèm từng skill.

Nguồn chính thức không đồng nghĩa với an toàn tuyệt đối. Hãy đọc `SKILL.md`,
script và nhãn `risk` trước khi chạy trong môi trường thật.

## Thêm skill

1. Tạo `skills/<skill-id>/SKILL.md` từ template.
2. Dùng tên kebab-case và bảo đảm `name` trùng tên folder.
3. Viết mô tả nêu rõ khả năng, tình huống kích hoạt và ranh giới sử dụng.
4. Khai báo đúng `risk`, `source` và license.
5. Chỉ thêm `scripts/`, `references/`, `assets/` khi chúng thực sự cần thiết.
6. Chạy `python tools/repo_skills.py all` và đọc báo cáo trước khi commit.

Chi tiết: [docs/contributing.md](docs/contributing.md).
