# 데이터셋 폴더 구조와 Metadata

기준: 2026-11-09 배포 구성 수정본.

이 문서는 논문의 Figure 6, Data Records와 GitHub 다운로드 구조를 설명합니다.
저장소와 데이터 ZIP은 비공개 준비본입니다. 공개 배포 권한이나 최종 라이선스가
확정됐다는 의미는 아닙니다.

## 1. 두 데이터 기록

| 구분 | 최상위 폴더 | 단위 | Train | Val | Test | 전체 |
|---|---|---|---:|---:|---:|---:|
| unified single-modal optical dataset | `public optical/` | 광학 이미지 1장 | 68,475 | 8,714 | 9,374 | 86,563 |
| multi-modal optical–thermal paired dataset | `paired_RGBT/` | 광학·열화상 1쌍 | 28,811 | 3,524 | 3,524 | 35,859 |

폴더 이름과 기록 식별자는 구분합니다. 기록 식별자는 각각
`public_optical_release_v1`, `paired_rgbt_v1`이며 변경하지 않았습니다.

단일모달 데이터셋은 FASDD_CV 66,480장, D-Fire 6,288장, CQU 6,244장,
Roboflow_FireSmoke 7,551장으로 구성되며 DFS는 제외돼 있습니다.
쌍 데이터셋은 실제 촬영 15,238쌍과 Unity 합성 20,621쌍으로 구성됩니다.
쌍 데이터셋에서 광학 뷰만 사용하는 optic-only 실험은 별도의 단일모달
광학 데이터셋과 같은 데이터 범위가 아닙니다.

## 2. Figure 6의 대표 폴더 구조

다음은 모든 ZIP을 새 빈 폴더에 풀었을 때의 대표 구조입니다.
`...`는 추가 출처·처리·검증 보조 파일의 생략을 뜻합니다.
GitHub의 일반 파일 목록에는 metadata, 분할 목록과 파일 목록이 있으며,
대용량 이미지·라벨은 별도 ZIP 첨부파일에 있습니다.

```text
public optical/
|-- README.md
|-- images/
|   |-- train/
|   |-- val/
|   `-- test/
|-- labels/
|   |-- train/
|   |-- val/
|   `-- test/
|-- metadata/
|   |-- manifest.csv
|   |-- classes.json
|   |-- summary.json
|   `-- ...
|-- splits/
|   |-- train.txt
|   |-- val.txt
|   `-- test.txt
`-- PAYLOAD_FILES.csv

paired_RGBT/
|-- README.md
|-- dataset/
|   |-- real/{experiment}/
|   |   |-- pair_optic/
|   |   |-- pair_thermal/
|   |   `-- pair_label/
|   `-- synthetic/{experiment}/
|       |-- pair_optic/
|       |-- pair_thermal/
|       `-- pair_label/
|-- labels/
|   |-- optic/{real,synthetic}/{experiment}/
|   `-- thermal/{real,synthetic}/{experiment}/
|-- metadata/
|   |-- manifest.csv
|   |-- classes.json
|   |-- summary.json
|   `-- ...
|-- splits/
|   |-- train.txt
|   |-- val.txt
|   `-- test.txt
`-- PAYLOAD_FILES.csv
```

Figure 6은 위 구조의 핵심 경로를 보여주는 개요도이며, 모든 보조 파일을
열거한 그림은 아닙니다. 수정본은 [편집 가능한 그림](../manuscript/figures/Figure6_Editable_Directory_Structure_20261109.pptx)과
[그림 미리보기](../manuscript/figures/Figure6_20261109.png)에서 확인할 수 있습니다.

## 3. Metadata 파일별 내용

| 파일 | 범위 | 내용 |
|---|---|---|
| `manifest.csv` | 두 데이터셋 | 개별 표본의 식별자, 분할, 경로, 해상도, 객체 수, 출처·실험, 이미지·라벨 해시 |
| `classes.json` | 두 데이터셋 | `0=fire`, `1=smoke` |
| `summary.json` | 두 데이터셋 | 표본·그룹·분할·출처 또는 도메인별 수량과 주석 통계. 모델 성능표가 아님 |
| `build_provenance.json` | 두 데이터셋 | 입력 metadata의 식별 해시, 내보내기 범위와 처리 이력 |
| `source_registry.csv` | 단일모달 | 원본 데이터 출처, 원출처 URL·DOI, 클래스 대응, 기록된 라이선스 등 |
| `source_deduplication_config.json` | 단일모달 | 중복 제거 설정, 출처 우선순위, 단계별 잔여 수량 |
| `source_split_summary.json` | 단일모달 | 원래 분할 설정과 출처별 통계 |
| `source_summary.json` | 쌍 데이터 | 실제·합성 구성, 실험별 분할과 제외 내역 등 원래 구축 요약 |
| `source_validation_recorded.json` | 쌍 데이터 | 기존 구축 시의 무결성·분할 검증 결과. 새로운 검사를 했다는 뜻은 아님 |
| `source_rights_review.csv` 등 | 두 데이터셋 | 출처별 권한 검토 상태. `PENDING`은 미확정 |
| `private_transfer.json` | 두 데이터셋 | 비공개 전송 범위와 원본/전송 manifest 연결 정보 |
| `metadata_preview_build_provenance.json` | 쌍 데이터 | 학습 라벨 해시 보완 전의 metadata 준비 이력 |

세부 필드 정의는 [데이터 사전](data_dictionary.md)을 따릅니다.
비어 있는 항목은 미확인·미기록일 수 있으며 숫자 0으로 해석하지 않습니다.

### 단일모달 manifest

한 행이 광학 이미지 한 장에 대응합니다. `record_id`, `split`,
`image_path`, `label_path`, `source_dataset`, `source_record_id`,
`width`, `height`, `classes`, `box_count`, `is_negative`,
`split_group_id`, 이미지·라벨 해시 등이 들어 있습니다.

### 쌍 데이터 manifest

한 행이 광학·열화상 한 쌍에 대응합니다. `sample_id`, `domain`,
`experiment`, `split`, 광학·열화상 경로, 해상도, 원본·학습용 라벨 경로와
각 해시가 들어 있습니다. 같은 식별자와 파일 stem으로 두 뷰의 대응을 보존합니다.

`source_label_sha256`는 원본 주석의 해시이며, `training_label_sha256`는
실제 동결 학습 라벨 바이트의 해시입니다. 두 종류의 주석을 서로 대체하지 않습니다.
실제 좌표는 CSV가 아니라 해당 YOLO `.txt` 라벨에 저장합니다.

## 4. 분할과 주석

`splits/train.txt`, `val.txt`, `test.txt`는 한 줄에 표본 식별자 하나를
기록하며 이미지 경로 목록이 아닙니다. 동결된 분할 순서와 구성은 유지합니다.

YOLO 주석 한 줄의 형식은 다음과 같습니다.

```text
class_id x_center y_center width height
```

좌표는 해당 이미지의 너비·높이로 정규화합니다.
단일모달 데이터에는 객체 상자가 0개인 이미지 41,364장이 포함됩니다.
쌍 데이터는 원본 주석에 대상 객체가 있는 쌍만 포함합니다.
합성 주석은 모델 보조 생성 이력이 있으므로 전체를 독립적인 수동 GT라고
표현하지 않습니다.

## 5. 이번 수정에서 제외한 것과 유지한 것

배포 파일과 Figure 6에서는 다음을 제외합니다.

- `SHA256SUMS_METADATA.txt`와 `*-SHA256SUMS.txt` 같은 별도 체크섬 목록.
- `registration.public.json` 정합 설정 파일.

다음은 그대로 보존합니다.

- 두 `manifest.csv`의 전체 내용과 해시 필드.
- `PAYLOAD_FILES.csv`의 이미지·라벨 경로, 크기와 해시.
- ZIP 목록 JSON의 압축 파일 크기와 SHA-256.
- 모든 이미지·라벨 바이트, 표본 식별자와 동결된 train/val/test 구성.
- 내부에 보관한 이전 검증 기록, 기존 ZIP과 원본 카메라 보정 자료.

정합 설정 파일을 배포에서 빼더라도 기존 열화상 뷰의 처리·정합은 취소되지
않습니다. 원시 온도 데이터나 모든 실제 촬영 환경의 완전한 보정값이 제공되는
것으로 설명하지 않습니다. 기준 깊이와 다른 깊이에는 잔여 시차가 있습니다.

현재 Git 파일과 다운로드 ZIP에서 제외하는 변경이며, 과거 Git 커밋을
삭제하거나 이력을 재작성하는 변경은 아닙니다.

## 6. 다운로드 시 주의사항

각 데이터셋의 `*-archives.json`에 나열된 ZIP 이름을 정확히 따릅니다.
첫 번째 ZIP의 수정본 이름에는 `metadata20261109`가 들어갑니다.
이전 첫 번째 ZIP과 수정본을 섞지 않고, 모든 ZIP을 같은 새 빈 폴더에 풉니다.
기존 폴더에 덮어 풀기만 하면 이번에 제외한 파일이 남을 수 있습니다.
나머지 23개 ZIP의 이미지·라벨 내용은 변경하지 않았습니다.

## 7. 논문용 Data Records 문안

The datasets comprise two records: the unified single-modal optical dataset,
stored under `public optical/`, and the multi-modal optical–thermal paired
dataset, stored under `paired_RGBT/`. In the single-modal record, optical images
and corresponding YOLO annotations are organised under
`images/{train,val,test}/` and `labels/{train,val,test}/`, respectively.
The paired record organises retained optical views, processed thermal views and
source annotations under `dataset/{real,synthetic}/{experiment}/`, using
`pair_optic/`, `pair_thermal/` and `pair_label/` subdirectories.
Canonical model-training annotations are stored separately under
`labels/{optic,thermal}/{real,synthetic}/{experiment}/`.

Both records include `metadata/` and `splits/` directories containing
sample manifests, class definitions, dataset summaries, provenance records and
frozen training, validation and test assignments. Each optical–thermal pair has
a common sample identifier. The paired manifest distinguishes source annotations
from canonical training annotations and retains their respective integrity
fields, `source_label_sha256` and `training_label_sha256`.
Figure 6 illustrates the principal directory structure after extraction of all
archive parts. Auxiliary provenance and inventory files are omitted from the
diagram for clarity.

## 8. Figure 6 caption

Fig. 6. Principal directory structures after archive extraction:
(a) the unified single-modal optical dataset and
(b) the multi-modal optical–thermal paired dataset.
Additional provenance and inventory files are omitted for clarity.

