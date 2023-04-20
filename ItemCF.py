# coding = utf-8

# 基于项目的协同过滤推荐算法实现
import random

import math
from operator import itemgetter

from app.models import Rating


class ItemBasedCF():
    # 初始化参数
    def __init__(self):
        # 找到相似的20个新闻，为目标用户推荐10个新闻
        self.n_sim_news = 50
        self.n_rec_news = 40

        # 将数据集划分为训练集和测试集
        self.trainSet = {}
        self.testSet = {}

        # 用户相似度矩阵
        self.news_sim_matrix = {}

        self.news_popular = {}  # 新闻受欢迎矩阵
        self.news_count = 0

        print('相似的新闻数 = %d' % self.n_sim_news)
        print('推荐的新闻数 = %d' % self.n_rec_news)

    # 读取“用户-新闻评分”数据   pivot 分割比例
    def get_dataset(self, ratings, pivot=0.75):
        trainSet_len = 0
        testSet_len = 0
        for rating in ratings:
            user = rating.userid   # 获取用户id
            news = rating.newsid   # 获取新闻id
            rating = rating.rating  # 获取评分
            if (random.random() < pivot):
                self.trainSet.setdefault(user, {})  # 对用户名为user的键添加一个空字典作为值，如果该键已存在，则将其对应的值保留不变。
                self.trainSet[user][news] = rating  # 在该用户的字典中，使用新闻的ID为键，将用户对该新闻的评分作为值存储。
                trainSet_len += 1
            else:
                self.testSet.setdefault(user, {})
                self.testSet[user][news] = rating
                testSet_len += 1
        # print(self.trainSet)
        print('划分训练集和测试集成功!')
        print('训练集长度 = %s' % trainSet_len)
        print('测试集长度 = %s' % testSet_len)

    # 首先，代码统计了每个新闻被多少个用户评价过，并将结果保存在字典self.news_popular中。
    # 然后，代码遍历每个用户评价的新闻，对于其中的每一对新闻，统计它们被同一个用户评价的次数，并将结果保存在字典self.news_sim_matrix中。
    # 接下来，代码遍历self.news_sim_matrix中的每一对新闻，并计算它们之间的相似度。
    # 如果有一个新闻的用户数为0，则将它们之间的相似度设置为0。否则，使用皮尔逊相关系数计算它们之间的相似度，并将结果保存在self.news_sim_matrix中。
    # 最后，代码输出计算相似度的结果，并返回self.news_sim_matrix。
    # 计算新闻之间的相似度
    def calc_news_sim(self):
        # 建立news_popular字典
        # 字典的items()方法返回一个包含字典所有键值对的元组数组
        for user, news in self.trainSet.items():
            for news in news:
                if news not in self.news_popular:
                    self.news_popular[news] = 0
                self.news_popular[news] += 1
        # print(self.news_popular)
        self.news_count = len(self.news_popular)  # 新闻个数
        print("新闻总个数 = %d" % self.news_count)  # 训练集 新闻总个数

        # 建立新闻共现矩阵
        for user, news in self.trainSet.items():
            # 遍历该用户每个新闻
            for m1 in news:
                # 遍历该用户每个新闻
                for m2 in news:   # 因为在某一篇新闻中，不应该出现两次相同的内容，因此需要保证生成的训练集中不会出现这种情况。
                    # 若该新闻为当前新闻，则跳过
                    if m1 == m2:
                        continue
                    self.news_sim_matrix.setdefault(m1, {})
                    self.news_sim_matrix[m1].setdefault(m2, 0)
                    self.news_sim_matrix[m1][m2] += 1 / math.log(1 + len(news))
        # print(self.news_sim_matrix)
        print("构建共同评定用户矩阵的成功!")  # Build co-rated users matrix success  即 a 对所有 为1

        # 计算新闻之间的相似性
        print("计算新闻相似性矩阵 ...")
        for m1, related_news in self.news_sim_matrix.items():
            for m2, count in related_news.items():
                # 注意0向量的处理，即某新闻的用户数为0，   2个新闻都得有
                if self.news_popular[m1] == 0 or self.news_popular[m2] == 0:
                    self.news_sim_matrix[m1][m2] = 0
                else:
                    # 基于两个新闻的流行度进行简单的加权平均  这段代码的基本逻辑是正确的，它实现了在训练集中统计每对新闻被相同用户评分的次数，并将相应的结果存储到 self.news_sim_matrix 中。
                    # 然后，它根据上一步中的结果计算新闻之间的相似性，使用的方法是基于两个新闻的流行度进行简单的加权平均
                    self.news_sim_matrix[m1][m2] = count / math.sqrt(self.news_popular[m1] * self.news_popular[m2])
        # print(self.news_sim_matrix)
        print('计算新闻相似性矩阵成功！')

    # 这段代码是基于物品的协同过滤算法中的推荐部分，用于为指定用户推荐新闻。
    # 首先，代码定义了两个变量K和N，分别表示相似度最高的K个新闻和推荐N个新闻。
    # 接下来，代码创建了一个字典rank，用于存储每个新闻的推荐度。
    # 然后，代码遍历了用户已经评价过的新闻，对于每个新闻，找到与之相似度最高的K个新闻，并计算它们的推荐度。
    # 具体来说，对于每个相似的新闻，代码判断它是否已经被用户评价过，如果是，则跳过；
    # 否则，将它的推荐度加上与之的相似度乘以已经评价过的新闻的评分。最后，代码返回按照推荐度排序后的前N个新闻，作为推荐结果。
    # 总的来说，这段代码的作用是基于用户已经评价过的新闻，推荐相似度最高的K个新闻中用户没有评价过的前N个新闻。
    # 针对目标用户U，找到K部相似的新闻，并推荐其N部新闻
    # 用户未产生过行为的新闻
    def recommend(self, user):
        K = self.n_sim_news
        N = self.n_rec_news
        # 用户user对新闻的偏好值
        rank = {}  # 存储推荐值
        # 用户user产生过行为的新闻，与新闻new按相似度从大到小排列，取与新闻new相似度最大的k个商品
        watched_news = self.trainSet[user]
        # print(watched_news)
        # 这段代码的作用是计算每个新闻的推荐度。rank是一个字典，用于存储每个新闻的推荐度。
        # 对于每个用户已经评价过的新闻，代码找到与之相似度最高的K个新闻，并计算它们的推荐度。
        # 具体来说，对于每个相似的新闻，代码判断它是否已经被用户评价过，如果是，则跳过；
        # 否则，将它的推荐度加上与之的相似度乘以已经评价过的新闻的评分。其中，related_news表示相似的新闻，w表示与之相似的相似度，
        # rating表示用户对已经评价过的新闻的评分。如果rank中不存在related_news这个新闻，则使用setdefault方法将其初始化为0。
        # 最终，返回的是一个列表，其中包含了对于指定用户的推荐结果。每个推荐结果是一个元组，包含了新闻的ID和推荐度。
        for news, rating in watched_news.items():
            # 遍历与新闻new最相似的前k个新闻，获得这些新闻及相似分数
            for related_news, w in sorted(self.news_sim_matrix[news].items(), key=itemgetter(1), reverse=True)[:K]:  # 获取与当前新闻最相似的前K篇新闻，w代表与当前新闻最相关的K篇新闻的相似度得分
                # 若该新闻为当前新闻，跳过
                if related_news in watched_news:
                    continue
                # 计算用户user对related_news的偏好值，初始化该值为0
                rank.setdefault(related_news, 0)

                # 排名的依据----》推荐新闻与该已看新闻的相似度（累计）*用户已看新闻的评分
                # 计算相关新闻的排名得分
                rank[related_news] += w * float(rating)  # w 表示权重值  ，rating 是一个评级值
                # print(rank)
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[:N]    # 取前n个值降序排列，获取第二个值

    # 首先，代码定义了一个变量N，表示每个用户推荐的新闻数量。接下来，代码定义了四个变量，分别用于统计准确率、召回率、推荐的新闻数量和测试集中的新闻数量。
    # 然后，代码遍历了所有的用户，对于每个用户，获取该用户在测试集中的新闻和基于物品的协同过滤算法推荐的新闻，
    # 计算准确率和召回率，并统计推荐的新闻数量和测试集中的新闻数量。同时，代码记录所有被推荐的新闻，以便计算覆盖率。
    # 最后，代码计算准确率、召回率和覆盖率，并输出评估结果。其中，准确率表示推荐的新闻中有多少是用户实际感兴趣的；
    # 召回率表示用户实际感兴趣的新闻有多少被成功推荐；覆盖率表示推荐系统能够覆盖多少不同的新闻。
    # 产生推荐并通过准确率、召回率和覆盖率进行评估
    def evaluate(self):
        print('Evaluating start ...')
        N = self.n_rec_news
        # 准确率和召回率
        hit = 0
        rec_count = 0
        test_count = 0
        # 覆盖率
        all_rec_news = set()
        # 首先，代码使用enumerate函数遍历了所有的用户，并使用get方法从测试集中获取该用户的测试数据。
        # 如果该用户没有测试数据，则使用一个空字典作为测试数据。然后，代码调用recommend方法为该用户推荐新闻。
        # 接下来，代码遍历推荐结果，对于每个推荐的新闻，判断它是否在测试数据中出现过，如果是，则将命中数加1，
        # 并将该新闻添加到覆盖的所有新闻中。同时，代码统计推荐的新闻数量和测试集中的新闻数量。
        # 最后，代码计算准确率、召回率和覆盖率，并输出评估结果。
        for i, user in enumerate(self.trainSet):   # i是一个计数器，用于记录当前遍历到的用户是第几个，user则是当前遍历到的用户对象
            test_news = self.testSet.get(user, {})   # 测试集上的new-rating
            rec_news = self.recommend(user)  # 推荐的新闻
            for news, w in rec_news:
                if news in test_news:
                    hit += 1   # 命中加1
                all_rec_news.add(news)  # 所有推荐的新闻
            rec_count += N   # 推荐的数量
            test_count += len(test_news)

        precision = hit / (1.0 * rec_count)   # 推荐中的正确数据(与真实数据相同的数据)与推荐数据之比
        recall = hit / (1.0 * test_count)  # 推荐中的正确数据(与真实数据相同的数据)与真实数据之比。
        coverage = len(all_rec_news) / (1.0 * self.news_count)  # u个用户的推荐集并集的物品数量与总物品数之比
        print('precisioin=%.4f\trecall=%.4f\tcoverage=%.4f' % (precision, recall, coverage))


if __name__ == '__main__':
    itemCF = ItemBasedCF()
    ratings = Rating.query.all()  # 评分数据集
    itemCF.get_dataset(ratings)  #
    itemCF.calc_news_sim()
    itemCF.evaluate()
