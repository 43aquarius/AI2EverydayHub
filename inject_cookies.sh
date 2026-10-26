#!/bin/bash
# 将用户 cookie 注入浏览器(逐个设置到 .xiaoheihe.cn 域)
COOKIE='lang=zh-cn; smidV2=202610162256586e1848f9b4f454982b22507ecb712596005019048c3995ea0; user_pkey=MTc5MjE2MjYzMS41M183NDY5MTkyOWVya3lkY3B4YmVzemlhcHQ__; user_heybox_id=74691929; heybox_id=74691929; pkey=MTc5MjE2MjYzMS41M183NDY5MTkyOWVya3lkY3B4YmVzemlhcHQ__; nickname=%u951D%u561A%u5F97; level=8; wa=0; wr=0; ws=%5B%5D; wj=%5B%5D; wc=1; wiki_power=0; permission=0; ac=0; br=0; bes=%5B%5D; bea=%5B%5D; beb=%5B%5D; bms=%5B%5D; bma=%5B%5D; bmb=%5B%5D; fss=0; fsa=0; fsb=0; x_xhh_tokenid=B1tdnIkWxHh3dFnAQuLlZw5RKxsTA5arrulOaaobpfUEfPT3osLQ7CmFEKdtFFLZna3CPL/GYgv3qMTNpaK9jCw%3D%3D'

IFS=';' read -ra ITEMS <<< "$COOKIE"
for item in "${ITEMS[@]}"; do
  name="${item%%=*}"
  name=$(echo "$name" | xargs)
  value="${item#*=}"
  [ -z "$name" ] && continue
  agent-browser cookies set "$name" "$value" --domain .xiaoheihe.cn >/dev/null 2>&1 && echo "set: $name"
done
echo "DONE"
