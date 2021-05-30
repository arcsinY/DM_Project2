import pandas as pd
import orangecontrib.associate.fpgrowth as oaf
import json as js
import matplotlib.pyplot as plt
import seaborn as sns

data = pd.read_csv('USvideos.csv', sep = ',')
# 转化category_id
with open('US_category_id.json') as f:
    json_date = js.load(f)
    f.close()
id2cat = {}
for i in range(len(json_date['items'])):
    id2cat[json_date['items'][i]['id']] = json_date['items'][i]['snippet']['title']
for i in range(len(data)):
    id = data.loc[i, 'category_id']
    data.loc[i, 'category_id'] = id2cat[str(id)]

# 转化views
arr = data['views']
one = arr.quantile(0.25)
three = arr.quantile(0.75)
view_level = []
for i in data['views']:
    if int(i) >= three:
        view_level.append('high view')
    elif int(i) <= one:
        view_level.append('low view')
    else:
        view_level.append('medium view')

# 转化likes和dislikes
like = []
for i in range(len(data)):
    if data.loc[i, 'likes'] >= data.loc[i, 'dislikes']:
        like.append('like')
    else:
        like.append('dislike')

# 转化comment_count
arr = data['comment_count']
one = arr.quantile(0.25)
three = arr.quantile(0.75)
comment_level = []
for i in data['comment_count']:
    if i >= three:
        comment_level.append('high comment')
    elif i <= one:
        comment_level.append('low comment')
    else:
        comment_level.append('medium comment')

data = data.drop(['views', 'likes', 'dislikes', 'comment_count'], axis = 1)
data.insert(0, 'views', view_level)
data.insert(0, 'like', like)
data.insert(0, 'comment_count', comment_level)
data = data.drop(['video_id', 'trending_date', 'publish_time', 'video_error_or_removed', 'description', 'thumbnail_link', 'title', 'comments_disabled', 'ratings_disabled'], axis = 1)

# 算法输入格式转换
id2str = {}   # 整数编码 —> 字符串
str2id = {}   # 字符串 -> 整数编码
id = 0
transaction = []
for i in range(len(data)):
    one = []
    for j in data.columns:
        # 拆分tags
        if j == 'tags':
            str_arr = data.loc[i, j].split('|')
            for s in str_arr:
                if s in str2id:
                    one.append(str2id[s])
                else:
                    id2str[id] = s
                    str2id[s] = id
                    one.append(id)
                    id += 1
        else:
            if data.loc[i, j] in str2id:
                one.append(str2id[data.loc[i, j]])
            else:
                id2str[id] = data.loc[i, j]
                str2id[data.loc[i, j]] = id
                one.append(id)
                id += 1
    transaction.append(one)

# 频繁项集
items = list(oaf.frequent_itemsets(transaction))
for i in items:
    freq_set = []
    abs_sup = i[1]
    for j in i[0]:
        freq_set.append(id2str[j])
    print(freq_set, abs_sup, round(float(abs_sup) / len(data), 2))

# 关联规则
rules = list(oaf.association_rules(dict(items), 0.2))
for i in rules:
    antecedent = []
    consequent = []
    for j in i[0]:
        antecedent.append(id2str[j])
    for j in i[1]:
        consequent.append(id2str[j])
    print(antecedent, "->", consequent, i[2], round(i[3],2))

# lift
measure = list(oaf.rules_stats(oaf.association_rules(dict(items), 0.2), dict(oaf.frequent_itemsets(transaction, 0.2)), len(data)))
for i in measure:
    antecedent = []
    consequent = []
    for j in i[0]:
        antecedent.append(id2str[j])
    for j in i[1]:
        consequent.append(id2str[j])
    print(antecedent, "->", consequent, round(i[6], 2))

# 计算Kulc
kulc = []
visit = [False for i in range(len(rules))]
for i in range(len(rules)):
    if visit[i] == True:
        continue
    visit[i] = True
    for j in range(len(rules)):
        if visit[j] == True:
            continue
        if rules[j][0] == rules[i][1] and rules[j][1] == rules[i][0]:
            one = []
            antecedent = []
            consequent = []
            for k in rules[i][0]:
                antecedent.append(id2str[k])
            for k in rules[i][1]:
                consequent.append(id2str[k])
            one.append(rules[i][0])
            one.append(rules[i][1])
            one.append((rules[i][3] + rules[j][3])/2)
            kulc.append(one)
            print('Kulc(', antecedent, consequent, ') = ', round((rules[i][3] + rules[j][3])/2, 2))
            visit[j] = True

# "like" 数量和 "low view" 数量
like_cnt = 0
low_view_cnt = 0
for i in data['like']:
    if i == 'like':
        like_cnt += 1
for i in data['views']:
    if i == 'low view':
        low_view_cnt += 1
print(like_cnt, low_view_cnt)

# 可视化
conf_matrix = []
lift_matrix = []
kulc_matrix = []
rules_column = set()

for i in range(len(measure)):
    rules_column.add(measure[i][0])
    
# 计算置信度矩阵
for i in rules_column:
    one = []
    for j in rules_column:
        if i == j:
            one.append(1)
        else:
            flag = False
            for k in range(len(rules)):
                if rules[k][0] == i and rules[k][1] == j:
                    one.append(rules[k][3])
                    flag = True
            if flag == False:
                one.append(0)
    conf_matrix.append(one)

# 计算lift矩阵
for i in rules_column:
    one = []
    for j in rules_column:
        if i == j:
            one.append(1)
        else:
            flag = False
            for k in range(len(measure)):
                if measure[k][0] == i and measure[k][1] == j:
                    one.append(measure[k][6])
                    flag = True
            if flag == False:
                one.append(0)
    lift_matrix.append(one)

# 计算kulc矩阵
for i in rules_column:
    one = []
    for j in rules_column:
        if i == j:
            one.append(1)
        else:
            flag = False
            for k in range(len(kulc)):
                if kulc[k][0] == i and kulc[k][1] == j:
                    one.append(kulc[k][2])
                    flag = True
            if flag == False:
                one.append(0)
    kulc_matrix.append(one)
# 改columns名字
rules_column_list = []
for i in rules_column:
    one = ""
    for j in range(len(i)):
        one += id2str[j]
        if j < len(i) - 1:
            one += ", "
    rules_column_list.append(one)
# 绘制热图的数据
rules_column = list(rules_column)
rules_column_list = []
for i in rules_column:
    one = ""
    for j in range(len(i)):
        one += id2str[list(i)[j]]
        if j < len(i) - 1:
            one += ", "
    rules_column_list.append(one)

lift_pd = pd.DataFrame(lift_matrix, columns = rules_column_list, index = rules_column_list)
plt.figure(figsize=(11, 9),dpi=100)
sns.heatmap(data = lift_pd, annot = True, fmt = ".2f")
plt.show()