# coding = utf-8

# 基于用户的协同过滤推荐算法实现
import random

import math
from operator import itemgetter

from app.models import Rating


class UserBasedCF():
    # 初始化相关参数
    def __init__(self):
        # 找到与目标用户兴趣相似的20个用户，为其推荐10部新闻
        self.n_sim_user = 20
        self.n_rec_news = 15

        # 将数据集划分为训练集和测试集
        self.trainSet = {}
        self.testSet = {}

        # 用户相似度矩阵
        self.user_sim_matrix = {}
        self.news_count = 0

        print('Similar user number = %d' % self.n_sim_user)
        print('Recommneded news number = %d' % self.n_rec_news)


    # 读取“用户-新闻”数据
    def get_dataset(self, ratings, pivot=0.75):
        trainSet_len = 0
        testSet_len = 0
        for rating in ratings:
            user = rating.userid
            news = rating.newsid
            rating = rating.rating
            if random.random() < pivot:
                self.trainSet.setdefault(user, {})
                self.trainSet[user][news] = int(rating)
                trainSet_len += 1
            else:
                self.testSet.setdefault(user, {})
                self.testSet[user][news] = int(rating)
                testSet_len += 1
        print('Split trainingSet and testSet success!')
        print('TrainSet = %s' % trainSet_len)
        print('TestSet = %s' % testSet_len)

    # 这段代码是一个基于用户的协同过滤推荐算法中计算用户相似度的过程。
    # 具体来说，代码首先构建了一个“新闻 - 用户”倒排索引，用于记录每个新闻被哪些用户浏览过。
    # 然后，对于每个新闻，找到浏览过该新闻的所有用户，对这些用户两两配对，
    # 累加它们共同浏览的新闻数量，最终得到一个“用户 - 用户”的共现矩阵
    # 。接着，通过计算每对用户之间的余弦相似度，得到一个“用户 - 用户”的相似度矩阵。
    # 这个相似度矩阵可以用于给用户推荐他们可能感兴趣的新闻。
    # 计算用户之间的相似度
    def calc_user_sim(self):
        # 构建“新闻-用户”倒排索引
        # key = newsID, value =  list of userIDs who have seen this news
        # 得到每个new被哪些user评价过
        print('Building news-user table ...')
        news_user = {}
        for user, news in self.trainSet.items():
            for news in news:
                if news not in news_user:
                    news_user[news] = set()
                news_user[news].add(user)
        print('Build news-user table success!')

        self.news_count = len(news_user)
        print('Total news number = %d' % self.news_count)

        print('Build user co-rated news matrix ...')
        for news, users in news_user.items():
            for u in users:
                for v in users:
                    if u == v:
                        continue
                    self.user_sim_matrix.setdefault(u, {})
                    self.user_sim_matrix[u].setdefault(v, 0)
                    self.user_sim_matrix[u][v] += 1 / math.log(1 + len(users))
        print(self.user_sim_matrix)
        print('Build user co-rated news matrix success!')

        # 计算相似性
        print('Calculating user similarity matrix ...')
        for u, related_users in self.user_sim_matrix.items():
            for v, count in related_users.items():
                # 这段代码是计算用户相似度的核心部分，其中user_sim_matrix[u][v]
                # 表示用户u与用户v之间的相似度。count表示用户u和用户v共同浏览过的新闻数量，len(self.trainSet[u])
                # 和len(self.trainSet[v])
                # 分别表示用户u和用户v浏览的新闻数量。代码中使用了余弦相似度公式计算用户相似度，具体来说，将count除以sqrt(
                #     len(self.trainSet[u]) * len(self.trainSet[v]))，得到的结果即为用户u和用户v之间的余弦相似度。
                #     余弦相似度范围在[-1, 1]
                # 之间，越接近1表示两个用户的兴趣越相似，可以被用于推荐系统中的用户相似度计算。
                self.user_sim_matrix[u][v] = count / math.sqrt(len(self.trainSet[u]) * len(self.trainSet[v]))

                # 这段代码是计算基于用户的协同过滤推荐算法中用户相似度的核心部分。具体来说，
                # count表示用户u和用户v共同浏览过的新闻数量，len(self.trainSet[u])
                # 和len(self.trainSet[v])
                # 分别表示用户u和用户v浏览的新闻数量。代码中使用了余弦相似度公式计算用户相似度，具体来说，将count除以sqrt(
                #     len(self.trainSet[u]) * len(self.trainSet[v]))，得到的结果即为用户u和用户v之间的余弦相似度。
                # 分母部分sqrt(len(self.trainSet[u]) * len(self.trainSet[v]))
                # 代表了用户u和用户v浏览新闻的数量之间的乘积的平方根。它与分子部分count代表了两个用户共同浏览新闻的数量，
                # 共同决定了用户之间的相似度。由于用户浏览的新闻数量不同，因此将两个用户浏览的新闻数量的乘积开根号，
                # 可以将两个用户之间的相似度归一化，
                # 使得它们之间的相似度值在[0, 1]
                # 之间。余弦相似度越接近1，表示两个用户之间的相似度越高。
        print('Calculate user similarity matrix success!')


    # 针对目标用户U，找到其最相似的K个用户，产生N个推荐
    def recommend(self, user):
        K = self.n_sim_user
        N = self.n_rec_news
        rank = {}
        watched_news = self.trainSet[user]

        # v=similar user, wuv=similar factor
        for v, wuv in sorted(self.user_sim_matrix[user].items(), key=itemgetter(1), reverse=True)[0:K]:
            for news, rvi in self.trainSet[v].items():
                if news in watched_news:
                    continue
                rank.setdefault(news, 0)
                rank[news] += wuv * rvi
        return sorted(rank.items(), key=itemgetter(1), reverse=True)[0:N]


    # 产生推荐并通过准确率、召回率和覆盖率进行评估
    def evaluate(self):
        print("Evaluation start ...")
        N = self.n_rec_news
        # 准确率和召回率
        hit = 0
        rec_count = 0
        test_count = 0
        # 覆盖率
        all_rec_news = set()

        for i, user, in enumerate(self.trainSet):
            test_news = self.testSet.get(user, {})
            rec_news = self.recommend(user)
            for news, w in rec_news:
                if news in test_news:
                    hit += 1
                all_rec_news.add(news)
            rec_count += N
            test_count += len(test_news)

        precision = hit / (1.0 * rec_count)
        recall = hit / (1.0 * test_count)
        coverage = len(all_rec_news) / (1.0 * self.news_count)
        print('precisioin=%.4f\trecall=%.4f\tcoverage=%.4f' % (precision, recall, coverage))


if __name__ == '__main__':
    userCF = UserBasedCF()
    ratings = Rating.query.all()
    userCF.get_dataset(ratings)
    userCF.calc_user_sim()
    userCF.evaluate()
