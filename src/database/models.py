from __future__ import annotations

from dataclasses import dataclass


ANIMAL_ITEM_FIELDS = (
    "noticeNo",
    "srvcTxt",
    "popfile4",
    "sprtEDate",
    "desertionNo",
    "rfidCd",
    "happenDt",
    "happenPlace",
    "kindCd",
    "colorCd",
    "age",
    "weight",
    "evntImg",
    "updTm",
    "endReason",
    "careRegNo",
    "noticeSdt",
    "noticeEdt",
    "popfile1",
    "processState",
    "sexCd",
    "neuterYn",
    "specialMark",
    "careNm",
    "careTel",
    "careAddr",
    "orgNm",
    "sfeSoci",
    "sfeHealth",
    "etcBigo",
    "kindFullNm",
    "upKindCd",
    "upKindNm",
    "kindNm",
    "popfile2",
    "popfile3",
    "popfile5",
    "popfile6",
    "popfile7",
    "popfile8",
    "careOwnerNm",
    "vaccinationChk",
    "healthChk",
    "adptnTitle",
    "adptnSDate",
    "adptnEDate",
    "adptnConditionLimitTxt",
    "adptnTxt",
    "adptnImg",
    "sprtTitle",
    "sprtSDate",
    "sprtConditionLimitTxt",
    "sprtTxt",
    "sprtImg",
    "srvcTitle",
    "srvcSDate",
    "srvcEDate",
    "srvcConditionLimitTxt",
    "srvcImg",
    "evntTitle",
    "evntSDate",
    "evntEDate",
    "evntConditionLimitTxt",
    "evntTxt",
)


@dataclass(frozen=True)
class DistrictCode:
    upr_cd: str
    org_cd: str
    name: str


@dataclass(frozen=True)
class ShelterRecord:
    care_reg_no: str
    care_name: str
    care_addr: str
    care_tel: str
    upr_cd: str
    org_cd: str
    lat: str
    lng: str
    save_target_animal: str
    raw: dict
