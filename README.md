# Render Remotion otomatis di GitHub

Upload project Remotion ke folder `projects/`, lalu GitHub Actions akan merendernya menjadi MP4.

## Upload project

Paling mudah dari HP: upload satu ZIP ke `projects/`, misalnya:

```text
projects/peter-episode1.zip
```

ZIP boleh berisi langsung `package.json`, `src/`, dan `public/`, atau dibungkus satu folder. Jangan sertakan `node_modules`.

Nama project hanya boleh memakai huruf, angka, titik, underscore, dan hyphen.

## Render otomatis

- Push yang menyentuh `projects/` akan merender project yang berubah.
- Hasil MP4 tersedia di **Actions → Artifacts**.
- Hasil MP4 juga dibuat sebagai **GitHub Release**.
- Render manual tersedia di **Actions → Render Remotion → Run workflow**.

Input manual:

- `project`: nama ZIP tanpa `.zip`, atau nama folder di `projects/`.
- `composition`: ID composition. Kosong berarti otomatis atau mengikuti `render.json`.

## render.json opsional

```json
{
  "entry": "src/index.ts",
  "composition": "PeterEpisode1",
  "args": []
}
```

## Catatan

Repository ini dibuat privat agar source dan video tidak terbuka untuk umum. Pastikan **Settings → Actions → General → Workflow permissions** mengizinkan Actions membuat Release.
