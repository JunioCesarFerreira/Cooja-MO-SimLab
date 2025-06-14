# Single Experiment

Neste diretório, apresentamos métodos e resultados de experimentos realizados com o Cooja. A ideia é verificar o comportamento de diferentes topologias e configurações dos motes no simulador, além de avaliar as métricas a serem utilizadas para análises e processamentos futuros.

## Organização

O diretório `build` contém os códigos e dados necessários para gerar configurações do Cooja e executar simulações. O processo é descrito no [arquivo](./build/README.md).
Os resultados e dados utilizadas em cada experimento estão nos dois diretórios `static` e `mobile`, sendo o primeiro para experimentos com redes estáticas, enquanto no segundo incluímos mobilidade.

- `static`
    - `rpl-udp-tsch`
    - `rpl-upd`

- `mobile`
    - `rpl-udp-tsch`
    - `rpl-upd`