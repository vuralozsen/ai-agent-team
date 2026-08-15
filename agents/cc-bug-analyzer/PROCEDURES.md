# Prosedürler

## Debugging Workflow

### Phase 1: Problem Understanding & Symptom Collection
1. Error messages ve stack traces topla
2. Expected behavior vs actual behavior anla
3. Relevant input data ve environment bilgisi topla
4. Problem reproducibility ve trigger conditions belirle

### Phase 2: Code Structure Analysis
1. Relevant code files'ları oku ve overall architecture'ı anla
2. Key functions ve data structures belirle
3. Call relationship graphs oluştur
4. Tüm olası execution path'leri işaretle

### Phase 3: Execution Flow Tracing
1. Entry point'ten başlayıp step-by-step trace et
2. Critical node'ları her adımda variable state'leri kaydet
3. Branch decision points ve condition evaluations belirle
4. Asynchronous operations ve callback execution order takip et

### Phase 4: Root Cause Localization
1. State'in expected'ten sapma yaptığı precise noktayı belirle
2. Değişikliği causing specific reason'ları analiz et
3. Root cause hypothesis'ini code logic reasoning ile doğrula
4. Diğer olası nedenleri elimine et

### Phase 5: Solution Verification
1. Root cause'i targeting minimal fix'ler önere
2. Fix sonrası execution flow changes'i reason et
3. Fix'in potansiyel side effects'lerini belirle
4. Relevant test cases önere
