# MEMORY POLICY

## Yazılacak
- Gelecekte başka agentın işine yarayacak bilgi
- Kalıcı kararlar, önemli teknik değişiklikler, known issue
- Deployment/infrastructure değişiklikleri, mimari etkileyenler
- Tekrar araştırılması gerekmeyecek kalıcı bilgi

## Yazılmayacak
- Sıradan konuşma, geçici düşünceler, basit cevaplar
- Bir defalık terminal çıktıları, ilgisiz araştırma
- Önemsiz dosya değişiklikleri, secret değerler

## Scope
GLOBAL (tüm projeler) | PROJECT (project_id) | DOMAIN (uzmanlık) | TASK (geçici, persist=false)

## Conflict
Eski kaydı silme; yeni kayıt oluştur, supersedes ilişkisi kur.
