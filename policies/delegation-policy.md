# DELEGATION POLICY
1. Bağımsız işler paralel, bağımlı işler sıralı.
2. Aynı dosyada conflict riski: lock / sequential / isolated worktree / explicit handoff.
3. Gereksiz agent spawn etme.
4. Nested delegation capability doğrulanmadan varsayılmaz.
5. Child agent'lar gereksiz tüm memory'yi görmez; sadece ilgili retrieval.
